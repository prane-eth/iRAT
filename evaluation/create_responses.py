#!/bin/env python3
# Get answer for each query and store in a file.

# add irat folder in the parent directory

from irat.utils.settings import env
from irat.utils.logger import log_debug, log_info, log_error, log_filename

import json
import os
import sys
import time

LLM_name = env('LLM_NAME')
if LLM_name is None:
	raise ValueError('LLM_NAME environment variable is not set.')
log_debug('LLM:', LLM_name)


# eval_name = 'human_eval'
# eval_name = 'mbpp'
eval_name = 'gsm8k'

start = 1 - 1
limit = 1319  # Dataset size for GSM8K is 1319, 165 for MBPP, and 164 for HumanEval.

# Switch to project's home directory
while not os.path.exists('README.md'):
	os.chdir('..')

ds_rows = []

if eval_name == 'human_eval':
	from human_eval.data import read_problems
	problems = read_problems()
	for prob in problems:
		ds_rows.append({
			'task_id': prob,
			'prompt': (  # v2 - bigcode-eval prompt
				f'Write functional code in Python according to the description.\n'
				f'Start your code with:\n' + problems[prob]['prompt']
				# References:
				# https://github.com/bigcode-project/bigcode-evaluation-harness/blob/main/bigcode_eval/tasks/humanevalpack.py#L651-L659
				# https://github.com/bigcode-project/bigcode-evaluation-harness/blob/main/bigcode_eval/tasks/humanevalpack_openai.py#L122
			),
		})
elif eval_name == 'mbpp':
	dataset_file = os.path.join('irat', 'processed', f'mbpp_proc.jsonl')
	with open(dataset_file) as file:
		for line in file:
			row = json.loads(line)
			task_id = row['id'].split('_')[1]
			row['task_id'] = int(task_id) - 600  # IDs start at 600

			# These indices are evaluated in old RAT paper.
			if 11 <= row['task_id'] <= 175:
				# get imports from row['code']
				# get all the lines if line.strip().startswith('import ')
				imports = []
				for line in row['code'].split('\n'):
					if line.strip().startswith('import '):
						imports.append(line.strip())
				row['test_imports'] = imports
				row['test_list'] = [line.strip() for line in row['tests'].split('\n') \
																		if line.strip()]
				prompt = (
					row['prompt'] + '\n'
					# 'Here are some sample test cases. Use the same function name and arguments.\n'
					'\n'.join(row['test_imports'] + row['test_list'][:1])
				)
				# References:
				# https://github.com/bigcode-project/bigcode-evaluation-harness/blob/main/bigcode_eval/tasks/mbpp.py#L48-L56
				ds_rows.append({
					'task_id': row['task_id'],
					'prompt': prompt,
					'test_imports': row['test_imports'],
					'test_list': row['test_list'],
					'mbpp_code': row['code'],
				})
elif eval_name == 'gsm8k':
	# Reference:
	# https://raw.githubusercontent.com/openai/grade-school-math/refs/heads/master/grade_school_math/data/test.jsonl
	dataset_file = os.path.join('irat', 'processed', f'gsm8k_testdata_github.jsonl')
	with open(dataset_file) as file:
		for line in file:
			stored_object = json.loads(line)
			ds_rows.append({
				'task_id': len(ds_rows) + 1,
				'prompt': stored_object['question'] + \
					'\n\n At the end, write the final answer after "####" at last.' \
					'\n For example, if the answer is ABC, write "#### ABC"',
				'correct_answer': stored_object['answer'],
			})
else:
	raise ValueError(f'Unknown evaluation dataset: {eval_name}')
log_debug(f'Loaded {eval_name} dataset - {len(ds_rows)} rows.')
dir_name = f'{eval_name}-responses-{LLM_name.replace(":", "-").replace("/", "-")}'
if os.path.exists('README.md'):  # In the project's home directory.
	os.chdir('evaluation')
	if not os.path.exists(dir_name):
		os.makedirs(dir_name)
	os.chdir(dir_name)
	log_debug(dir_name)


# Import after switching to other directory
# This ensures the logs created by the modules are stored in the relevant directory.
from irat.utils.common_functions import print_separator
from irat.utils.prompt_security import UnsafePromptError
from irat.utils.ratelimit_counter import reset_ratelimit_wait_time

from irat.initial_drafting import generate_initial_draft
from irat.old_rat import rat as old_rat
from irat.pipeline import run_pipeline
from irat.retrieval import get_used_retrievals, reset_budget


def errors_exist():
	try:
		with open('error.txt') as file:
			error_text = file.read()
		if error_text:
			log_debug('Error exists in error.txt. Please resolve an delete the file.')
			log_debug(error_text.split('key=')[0])
			return error_text
	except:
		pass

if errors_exist():
	sys.exit(1)

pass_k = 1  # We use pass@1 for HumanEval and MBPP.
if eval_name == 'gsm8k':  # Avoid pass@k and use only 1 response.
    pass_k = 1

for index, ds_data_row in enumerate(ds_rows[start:limit], start=start+1):
	print(index)
	out_file = f'test_{index}.json'
	data_object = ds_data_row.copy()
	save_file = lambda : json.dump(data_object, open(out_file, 'w'), indent='\t')
	if errors_exist():
		break

	if os.path.exists(out_file):
		log_info(f'File {out_file} already exists. Loading...')
		with open(out_file) as file:
			stored_object = json.load(file)
			if stored_object:
				data_object.update(stored_object)
		log_info(f'Loaded data for query {index}', stored_object['prompt'][:30] + '...')

	query = data_object['prompt'].strip()
	log_info(f'Processing query {index}: {query[:50]}...')

	# Create a "responses" list of length k if it doesn't exist.
	if 'responses' not in data_object:
		data_object['responses'] = []
	while len(data_object['responses']) < pass_k:
		data_object['responses'].append({})

	if errors_exist():
		break
	errors = False
	for k_index, data_row in enumerate(data_object['responses'][:pass_k], start=1):

		# draft_1 is shared by both iRAT and old RAT.
		# Short responses lack reasoning and should be re-generated.
		# Handling short responses is the limitation not handled by old-RAT.
		draft_1 = generate_initial_draft(query)
		if errors_exist():
			errors = True
			break
		save_file()

		if not data_row.get('old_rat_answer'):
			print_separator('Using old RAT')
			reset_ratelimit_wait_time()
			reset_budget()
			start_time = time.time()

			# Run old-RAT by loggging to the file
			with open(log_filename, 'a') as f:
				old_stderr = sys.stderr
				sys.stderr = f
				try:
					_, old_rat_answer, old_rat_revisions = old_rat(query, draft_1)
				finally:
					sys.stderr = old_stderr

			data_row['old_rat_answer'] = old_rat_answer
			data_row['old_rat_retrievals'] = get_used_retrievals()
			if errors_exist():
				errors = True
				break
			save_file()

		if not data_row.get('final_answer'):
			log_info(f'Running iRAT pipeline for query {index}.{k_index}...')
			reset_ratelimit_wait_time()
			reset_budget()
			start_time = time.time()

			try:
				draft_1, draft_2, evaluator_feedback, \
						final_answer = run_pipeline(query, draft_1)
				log_info(f'Query {index}.{k_index} processed successfully.')
			except UnsafePromptError as e:
				log_error(f'Unsafe prompt for query {index}.{k_index}. Skipping.')
				print_separator()
				data_object['unsafe_prompt'] = True
				save_file()
				break
			except Exception as e:
				log_error(f'No response for query. Error:')
				log_error(e)
				print_separator()
				continue

			data_row['final_answer'] = final_answer
			data_row['retrievals'] = get_used_retrievals()
			if errors_exist():
				errors = True
				break
			save_file()


	log_info(f'Saved results to {dir_name}/{out_file}')
	print_separator()
	if errors:
		log_error('Errors occurred during processing. Stopping further processing.')
		break
	log_debug()  # empty line

log_info('Process completed. You may now change the dataset.')
