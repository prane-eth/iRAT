# Filter the dataset to using only coding-related rows, 
# making it relevant to datasets such as HumanEval and MBPP.

from datasets import load_dataset, DatasetDict
import os

dataset = load_dataset('microsoft/ms_marco', 'v2.1', streaming=False)
# set streaming=False to download the entire dataset, or streaming=True to stream it without downloading
# https://huggingface.co/datasets/microsoft/ms_marco/viewer/v2.1/
# subsets: 'train', 'validation', 'test'


# to get the files, run - !python 1_get_coding_rows.py
base_dir = 'data'
if not os.path.exists(base_dir):
	print(f'Directory {base_dir} does not exist. Running 1_get_coding_rows.py to create it.')
	os.system('python 1_get_coding_rows.py')

indices = {}
for subset in dataset:  # 'train', 'validation', 'test'
	indices[subset] = set()
	file_path = os.path.join(base_dir, f'coding_rows_{subset}.txt')
	with open(file_path, 'r') as f:
		# file format: "1: text here \n2: text here \n3: text here \n"
		for line in f:
			line = line.strip()
			if not line:
				continue
			index, text = line.split(':', 1)
			index = int(index.strip())
			indices[subset].add(index)

	if not indices[subset]:
		raise ValueError(f'No coding indices found in the file of {subset} subset.')
	print(f'Loaded {len(indices[subset])} {subset} indices from the file.')

# Filter the dataset to only include coding rows
coding_dataset = {}
for subset in dataset:
	coding_dataset[subset] = dataset[subset].filter(
		lambda example, index: index in indices[subset],
		with_indices=True
	)
print(f'Filtered dataset contains {len(coding_dataset["train"])} rows.')

print('Sample coding rows:')
for i, row in enumerate(coding_dataset['train']):
	if i >= 5:  # Display only the first 5 rows
		break
	print(f'Row {i}')
	print(f'  Query: {row["query"]}')

# Save filtered coding_dataset for easy reload
coding_ds = DatasetDict(coding_dataset)
coding_ds.save_to_disk('coding_dataset')

# # To push the dataset to Hugging Face Hub (private repository)
# repo_id = 'prane-eth/msmarco_coding'
# from huggingface_hub import HfApi
# from dotenv import load_dotenv
# load_dotenv('.env.main')  # my own file, not shared

# api = HfApi(token=os.getenv('HF_TOKEN'))
# api.upload_folder(folder_path='coding_dataset',
#     repo_id=repo_id, repo_type='dataset')

# print(f'Dataset successfully pushed to https://huggingface.co/{repo_id}')
