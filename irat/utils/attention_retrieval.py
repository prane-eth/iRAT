
from datasets import load_from_disk

# restores the same DatasetDict with train/validation splits
dataset = load_from_disk('coding_dataset')
if not len(dataset['train']) or not len(dataset['validation']):
	raise ValueError('The training dataset is empty. Please check the dataset creation process.')

from sentence_transformers import CrossEncoder

model_name = 'cross-encoder/ms-marco-MiniLM-L6-v2'  # 22.7M params - 3.3M downloads on Huggingface
model_name_short = 'miniLM-L6-v2'

model = CrossEncoder(model_name)

def predict(passages: list[str], query: str) -> list[float]:
	# Query the LLM with a list of passages and a query.
	# Returns a list of scores for each passage.
	scores = model.predict([(query, passage) for passage in passages], batch_size=1)
	scores = scores.tolist()
	return scores

top_n = 3
min_score_threshold = 0.0
score_threshold = 8.0


def classify(predictions: list[float]) -> list[bool]:
	if not predictions:
		raise ValueError('Model predictions list is empty')
	scores_dict = { index: score for index, score in enumerate(predictions)
					if score > min_score_threshold }
	top_scores = sorted(scores_dict.items(), key=lambda x: x[1], reverse=True)[:top_n]
	selected_indices = [index for index, score in top_scores
						if score > score_threshold]
	# return True for selected indices, False for others
	result = [index in selected_indices for index in range(len(predictions))]
	if len(result) != len(predictions):
		raise ValueError(f'Length of result {len(result)} does not match length of scores {len(predictions)}')
	return result

def get_selected_indices(query, passage_texts):
	predictions = predict(passage_texts, query)
	# select passages based on predictions without deciding thresholds
	classifications = classify(predictions)
	selected_indices = []
	for index, pred in enumerate(classifications):
		if pred:
			selected_indices.append(index)
	return selected_indices

