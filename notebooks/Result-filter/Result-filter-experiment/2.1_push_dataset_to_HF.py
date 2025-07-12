# To push the dataset to Hugging Face Hub (private repository)
from dotenv import load_dotenv
from huggingface_hub import HfApi
import os

load_dotenv('../../../.env.main')

repo_id = 'prane-eth/msmarco_programming'
folder = 'coding_dataset'

api = HfApi(token=True)  # Automatically uses the token from the environment variable HF_TOKEN


# Check if the repository exists, and create it if it doesn't
try:
	api.repo_info(repo_id=repo_id, repo_type='dataset')
	print(f'Repository {repo_id} exists. Deleting...')
	api.delete_repo(repo_id=repo_id, repo_type='dataset')
except:
	pass

api.create_repo(repo_id=repo_id, repo_type='dataset', private=True)
print(f'Repository {repo_id} created successfully.')

base_dir = 'data'
if not os.path.exists(base_dir):
	# os.system('python 1_get_coding_rows.py')
	raise Exception(f'Directory {base_dir} does not exist. Running 1_get_coding_rows.py to create it.')
os.chdir(base_dir)

readme_md = '''
# MS MARCO - Programming Subset
This dataset is a **subset** of the original Microsoft [MS MARCO dataset](https://huggingface.co/datasets/microsoft/ms_marco).
It carries forward all of MS MARCO's licensing and usage requirements.
For License, Terms & Conditions, and more information, visit https://huggingface.co/datasets/microsoft/ms_marco.

## To load the dataset:
```python
from datasets import load_from_disk
dataset = load_from_disk('coding_dataset')
```

## Citation
If you use this subset in your work, please cite the original MS MARCO paper: 

```bibtex
@article{DBLP:journals/corr/NguyenRSGTMD16,
	author    = {Tri Nguyen and Mir Rosenberg and Xia Song and
				Jianfeng Gao and Saurabh Tiwary and 
				Rangan Majumder and Li Deng},
	title     = {{MS} {MARCO:} {A} Human Generated MAchine Reading COmprehension Dataset},
	journal   = {CoRR},
	volume    = {abs/1611.09268},
	year      = {2016},
	url       = {http://arxiv.org/abs/1611.09268},
	archivePrefix = {arXiv},
	eprint    = {1611.09268},
	timestamp = {Mon, 13 Aug 2018 16:49:03 +0200},
	biburl    = {https://dblp.org/rec/journals/corr/NguyenRSGTMD16.bib},
	bibsource = {dblp computer science bibliography, https://dblp.org}
}
```
'''
readme_path = os.path.join(folder, 'README.md')
with open(readme_path, 'w', encoding='utf-8') as f:
	f.write(readme_md)
api.upload_folder(folder_path=folder, repo_id=repo_id, repo_type='dataset')

print(f'Dataset successfully pushed to https://huggingface.co/datasets/{repo_id}')

'''
from dotenv import load_dotenv
load_dotenv()
hf_token = os.getenv('HF_TOKEN')
if not hf_token:
	raise ValueError("HF_TOKEN environment variable is not set. Please set it in your .env.main file.")

from datasets import load_dataset
dataset = load_dataset('prane-eth/msmarco_programming', token=hf_token)
'''
