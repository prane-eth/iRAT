# The below code is about a classifier that predicts selection of a paragraph based on its scores.

from sklearn.linear_model import LogisticRegression
import numpy as np

# Train a model to predict the selection status based on the scores.
print(f'Training the model...')
classifier = LogisticRegression(random_state=seed)

# Reshape all_scores to a 2D array
train_scores_np = np.array(all_scores['train']).reshape(-1, 1)
classifier.fit(train_scores_np, all_selection_statuses['train'])

# Test the model using all the rows
training_classifications = classifier.predict(train_scores_np)
# if all values are 0, print the same
if np.all(training_classifications == 0):
	print('Warning: All training classifications are 0.')
accuracy = (training_classifications == all_selection_statuses['train']).mean()
print(f'Train data accuracy: {accuracy:.2%}')

# Test the model on the validation set
validation_scores_np = np.array(all_scores['validation']).reshape(-1, 1)
validation_classifications = classifier.predict(validation_scores_np)
if np.all(validation_classifications == 0):
	print('Warning: All validation classifications are 0.')
validation_accuracy = (validation_classifications == all_selection_statuses['validation']).mean()
print(f'Validation accuracy: {validation_accuracy:.2%}')

def classify(scores: list[float]) -> list[bool]:
    return classifier.predict(np.array(scores).reshape(-1, 1))



#### Train a neural network
# to predict the selection of paragraphs based on the scores

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split

# Build a dataset of row‐wise, fixed‐length vectors:
#    - Pad each `score_list` to length 10 with zeros.
#    - Pad each `label_list` to length 10 with zeros (treat “nonexistent” passages as label=0).
train_rows = []  # will hold lists of length=10
train_row_labels = []

# Pre-process the training data
for score_list, label_list in zip(all_scores['train'], all_selection_statuses['train']):
	# Example: score_list: e.g. [3.75, -5.70, 3.06, ...] length <= 10
	# label_list: e.g. [0, 1, 0, ...]   same length
	L = len(score_list)
	assert L <= max_passages, f'Found a row with {L} passages, exceeds max_passages={max_passages}'

	# Ensure both lists are of length `max_passages`
	score_list = score_list + [0.0] * (max_passages - L)
	label_list = label_list + [0] * (max_passages - L)

	train_rows.append(score_list)
	train_row_labels.append(label_list)

# Perform train/val split
X_train, X_val, y_train, y_val = train_test_split(
	train_rows, train_row_labels,
	test_size=0.2,
	random_state=seed,
)
# For now, use all rows for training, and some rows for validation.
X_train = train_rows
y_train = train_row_labels

class RowDataset(Dataset):
	def __init__(self, rows, labels):
		'''
		rows:   List of lists, each list of length = max_passages (floats)
		labels: List of lists, each list of length = max_passages (int 0/1)
		'''
		assert len(rows) == len(labels), 'Rows and labels must have the same length.'
		self.X = torch.tensor(rows, dtype=torch.float32)       # shape: (N, 10)
		self.y = torch.tensor(labels, dtype=torch.float32)     # shape: (N, 10)

	def __len__(self):
		return len(self.X)

	def __getitem__(self, idx):
		return self.X[idx], self.y[idx]

train_ds = RowDataset(X_train, y_train)
val_ds   = RowDataset(X_val,   y_val)

batch_size = 32
train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
						  worker_init_fn=lambda x: random.seed(seed + x))
val_loader   = DataLoader(val_ds,   batch_size=batch_size)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

net = nn.Sequential(
	nn.Linear(max_passages, 64),
	nn.ReLU(),
	nn.Linear(64, 32),
	nn.ReLU(),
	nn.Linear(32, max_passages),
	nn.Sigmoid()
).to(device)

# Use BCE after Sigmoid. Since we used Sigmoid in the last layer:
criterion = nn.BCELoss(reduction='mean')
# (BCELoss expects input 0-1 and target 0/1, computing elementwise loss
#  and then mean over all elements)

optimizer = torch.optim.Adam(net.parameters(), lr=1e-3)
threshold = 0.5  # Minimum threshold for classification as True/False

for epoch in range(30):  # Training
	net.train()
	total_loss = 0.0
	for X, y in train_loader:
		X = X.to(device)
		y = y.to(device)

		optimizer.zero_grad()
		preds = net(X)
		loss = criterion(preds, y)
		loss.backward()
		optimizer.step()

		total_loss += loss.item() * X.size(0)

	avg_train_loss = total_loss / len(train_ds)

	# Validation
	net.eval()
	val_loss = 0.0
	correct = 0
	total = 0
	with torch.no_grad():
		for X, y in val_loader:
			X = X.to(device)
			y = y.to(device)
			val_preds = net(X)
			val_loss += criterion(val_preds, y).item() * X.size(0)

			# Compute accuracy per‐entry (i.e. how many of the 10 positions match exactly)
			predicted_bits = (val_preds >= threshold).float()
			correct += (predicted_bits == y).sum().item()
			total += y.numel()
	
	avg_val_loss = val_loss / len(val_ds)
	val_acc = correct / total   # fraction of correctly predicted passage‐labels overall
	print(
		f'Epoch {epoch+1:2d}  TrainLoss: {avg_train_loss:.4f}  '
		f'ValLoss: {avg_val_loss:.4f}  ValAcc: {val_acc:.4f}'
	)

def classify(scores: list[float]) -> list[bool]:
	'''
	Given `scores`, a Python list of floats (length ≤ max_passages),
	pad to length=max_passages with zeros, run through `net`,
	then return only the first len(scores) booleans.
	'''
	net.eval()
	L = len(scores)
	assert L <= max_passages, f'Input length {L} > max_passages={max_passages}'

	padded = scores + [0.0] * (max_passages - L)  # Ensure length=max_passages
	tensor_row = torch.tensor(padded, dtype=torch.float32, device=device).unsqueeze(0)  # shape (1,10)

	with torch.no_grad():
		out_probs = net(tensor_row).squeeze(0)   # shape (10,)

	# Convert to bools with threshold, then take first L entries
	out_bools = (out_probs >= threshold).cpu().numpy().astype(bool).tolist()
	return out_bools[:L]