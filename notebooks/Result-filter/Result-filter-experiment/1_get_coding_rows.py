### Get the indices of coding-related rows to make the model focus
### 	on the selected datasets such as HumanEval and MBPP.
from datasets import load_dataset

import os
base_dir = 'data'
if not os.path.exists(base_dir):
	os.makedirs(base_dir)

dataset = load_dataset('microsoft/ms_marco', 'v2.1')

coding_keywords = [
	'python', 'java', 'JS', 'c++', 'css', 'html', 'typescript', 'php', 
	'Swift', 'kotlin', 'perl ', 'sql', 'matlab', 'objective-c', 'c#', 
	'fortran', 'cobol', 'vba', 'groovy', 'haskell', 'clojure', 'f#', 
	'solidity', 'xml', 'json', 'yaml', 'protobuf', 'graphql', 'django', 
	'laravel', 'node.js', 'tensorflow', 'pytorch', 'keras', 'numpy', 
	'scikit-learn', 'sklearn', 'hadoop', 'kubernetes', 'docker', 'ansible', 
	'terraform', 'azure', 'AWS', 'gcp', 'linux', 'unix', 'Git', 
	'github', 'gitlab', 'bitbucket', 'jenkins', 'travis', 'circleci', 'maven', 
 	'gradle', 'webpack', 'babel', 'redux', 
	'data structure', 'object-oriented', 'functional programming', 
	'algorithm', 'API', 'REST', 'GraphQL', 'microservices', 'serverless', 
]
# Remaining keywords such as 'pandas', 'angular', etc are not included as they have a real meaning.
# Some characters should be in upper case to avoid confusion with other words.
# For example, 'aws' is present in 'laws' but 'AWS' is not.
# Some words should start or end with a space to avoid confusion with other words.
# For example, 'perl' is present in 'properly' but 'perl ' is not.

def is_coding_related(query):
	# Why compare by the query but not the passages? Because coding questions can include spammy results, 
	# which don't show whether a row is related to coding. We compare by 'query' which shows the user intent.
	for keyword in coding_keywords:
		if keyword in query or keyword in query.lower():
			return True
	return False

for subset in dataset:  # 'train', 'validation', 'test'
	coding_rows_file = os.path.join(base_dir, f'coding_rows_{subset}.txt')
 
	coding_row_count = 0

	with open(coding_rows_file, 'w+') as f:
		f.truncate(0)  # clear the file
		for index, row in enumerate(dataset[subset]):
			if not is_coding_related(row['query']):
				continue
			row_text = f'{index}: {row["query"]}'
			print(row_text, file=f)
			coding_row_count += 1

	print(f'{coding_row_count} coding-related rows of type "{subset}" saved to', coding_rows_file)

# Why write to a file instead of directly creating a dataset?
# Writing to a file allows us to easily inspect the rows and
# 	ensure that the filtering is correct before creating a dataset.
