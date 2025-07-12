import os
from typing import Generator

# Change to the directory of this script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from datasets import load_from_disk
dataset = load_from_disk('coding_dataset')


results = {}

def mark_as_correct(index, score=1.0):
	results[str(index)] = score

def mark_as_incorrect(index):
	results[str(index)] = False

def get_accuracy():
	total_evaluated = len(results)
	total_correct = sum(results.values())
	# print(f'Total evaluated: {total_evaluated}, Total correct: {total_correct}')
	return total_correct / total_evaluated if total_evaluated > 0 else 0

def select_paragraphs(model, query: str, paragraphs: list[str], top_k: int) -> Generator[int, None, None]:
	for result in model.rank(query, paragraphs, top_k):
		yield result['corpus_id'], result['score']


## Evaluation
subset = 'validation'  # 'test' subset in MARCO doesn't mention the correct answers.

def evaluate_model(model, model_name_short):
	results.clear()  # Reset results for each evaluation
	for query_index, row in enumerate(dataset[subset]):
		correct_indices = [index for index, x in enumerate(row['passages']['is_selected']) if x > 0]
		if not correct_indices:  # If R=0, we can't divide by R.
			# No correct indices. We need not select anything.
			mark_as_correct(query_index)
			continue

		# Select indices using the model
		selected_rows = select_paragraphs(model, row['query'], row['passages']['passage_text'], 
											top_k=len(correct_indices))
		selected_indices = []
		for index, score in selected_rows:
			selected_indices.append(index)
		total_correct = len(correct_indices)
		correct_selected = len([index for index in selected_indices if index in correct_indices])
		score = correct_selected / total_correct  # Not divided by 0. We handled case of no correct indices above.
		if score:
			mark_as_correct(query_index, score)
		else:
			mark_as_incorrect(query_index)

	accuracy = get_accuracy()
	print(f'Accuracy: {accuracy:.2%}')
	if model_name_short:
		print(f'Model: {model_name_short}')
		with open('scores.txt', 'a') as f:
			f.write(f'{model_name_short} - accuracy: {accuracy:.2%}\n')

	return accuracy



# Supports to use k+1 and a custom threshold for filtering results.
def evaluate_model_2(model, model_name_short, add_r=1, threshold=6.0): # add_r to implement "R+1"
	results.clear()  # Reset results for each evaluation
	for query_index, row in enumerate(dataset[subset]):
		correct_indices = [index for index, x in enumerate(row['passages']['is_selected']) if x > 0]
		if not correct_indices:  # If R=0, we can't divide by R.
			# No correct indices mentioned. We need not select anything.
			mark_as_correct(query_index)
			continue

		# Select top-R indices using the model
		R = len(correct_indices)  # Upto 1 for coding rows.
		selected_rows = select_paragraphs(model, row['query'], row['passages']['passage_text'], 
											top_k=R + add_r) # Get the top-k scores
		# Filter based on the threshold
		filtered_indices = []
		for index, score in selected_rows:
			if score > threshold:
				filtered_indices.append(index)

		correct_selected = len([index for index in filtered_indices if index in correct_indices])
		score = correct_selected / R  # Not divided by 0. We handled case of no correct indices above.
		if score:
			mark_as_correct(query_index, score)
		else:
			mark_as_incorrect(query_index)

	accuracy = get_accuracy()
	print(f'Accuracy: {accuracy:.2%}')
	if model_name_short:
		print(f'Model: {model_name_short}')
		with open('scores.txt', 'a') as f:
			f.write(f'{model_name_short} - accuracy: {accuracy:.2%}\n')

	return accuracy


if __name__ == '__main__':
	# Example usage
	from sentence_transformers import CrossEncoder
	model_name = 'cross-encoder/ms-marco-MiniLM-L6-v2'
	# model_name = 'cross-encoder/ms-marco-MiniLM-L4-v2'
	# model_name = 'mixedbread-ai/mxbai-rerank-xsmall-v1'
	model = CrossEncoder(model_name)
	evaluate_model(model, model_name_short=None)
