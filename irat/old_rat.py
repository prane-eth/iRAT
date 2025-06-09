# This file allows to call old RAT as a single function to pass the query and get the final response.

# Credits: https://github.com/CraftJarvis/RAT

from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(override=True)

openai = OpenAI()

LLM_model = os.getenv('LLM_NAME')
KNOWLEDGE_CUTOFF = os.getenv('KNOWLEDGE_CUTOFF')

# Basic Tool Functions

def user_message(content, role='user'):
	return {
		'role': role,
		'content': content
	}

def system_message(content):
	return user_message(content, role='system')

def assistant_message(content):
	return user_message(content, role='assistant')

from langchain.tools import Tool
from langchain_community.utilities import GoogleSearchAPIWrapper
def get_search(query:str='', k:int=1):  # get the top-k resources with google
	search = GoogleSearchAPIWrapper(k=k)
	def search_results(query):
		return search.results(query, k)
	tool = Tool(
		name='Google Search Snippets',
		description='Search Google for recent results.',
		func=search_results,
	)
	ref_text = tool.run(query)
	if 'Result' not in ref_text[0].keys():
		return ref_text
	else:
		return None

from langchain_community.document_transformers import Html2TextTransformer
from langchain_community.document_loaders import AsyncHtmlLoader
def get_page_content(link:str):
	loader = AsyncHtmlLoader([link])
	docs = loader.load()
	html2text = Html2TextTransformer()
	docs_transformed = html2text.transform_documents(docs)
	if len(docs_transformed) > 0:
		return docs_transformed[0].page_content
	else:
		return None

import tiktoken
def count_tokens(string: str, encoding_name: str = 'cl100k_base') -> int:
	'''Returns the number of tokens in a text string.'''
	encoding = tiktoken.get_encoding(encoding_name)
	num_tokens = len(encoding.encode(string))
	return num_tokens

def chunk_text_by_sentence(text, chunk_size=2048):
	'''Chunk the $text into sentences with less than 2k tokens.'''
	sentences = text.split('. ')
	chunked_text = []
	curr_chunk = []
	# Add text snippets sentence by sentence, making sure each paragraph is less than 2k tokens
	for sentence in sentences:
		if count_tokens('. '.join(curr_chunk)) + count_tokens(sentence) + 2 <= chunk_size:
			curr_chunk.append(sentence)
		else:
			chunked_text.append('. '.join(curr_chunk))
			curr_chunk = [sentence]
	# Add the last snippet
	if curr_chunk:
		chunked_text.append('. '.join(curr_chunk))
	return chunked_text[0]

def chunk_text_front(text, chunk_size = 2048):
	'''
	get the first `trunk_size` token of text
	'''
	tokens = count_tokens(text)
	if tokens < chunk_size:
		return text
	else:
		ratio = float(chunk_size) / tokens
		char_num = int(len(text) * ratio)
		return text[:char_num]

def chunk_texts(text, chunk_size = 2048):
	'''
	trunk the text into n parts, return a list of text
	[text, text, text]
	'''
	tokens = count_tokens(text)
	if tokens < chunk_size:
		return [text]
	else:
		n = int(tokens/chunk_size) + 1
		# Calculate the length of each section
		part_length = len(text) // n
		# If it is not divisible, the last part will contain extra characters.
		extra = len(text) % n
		parts = []
		start = 0

		for i in range(n):
			# For the first extra parts, one more character is allocated to each part
			end = start + part_length + (1 if i < extra else 0)
			parts.append(text[start:end])
			start = end
		return parts

# RAT Pipeline

from datetime import datetime
chatgpt_system_prompt = f'''
You are  a large language model with knowledge cutoff: {KNOWLEDGE_CUTOFF}.
Current date: {datetime.now().strftime('%Y-%m-%d')}
'''

draft_prompt = '''
IMPORTANT:
Try to answer this question/instruction with step-by-step thoughts and make the answer more structural.
Use `\n\n` to split the answer into several paragraphs.
Just respond to the instruction directly. DO NOT add additional explanations or introducement in the answer unless you are asked to.
'''
def get_draft(question):
	# Getting the draft answer
	draft = openai.chat.completions.create(
		model=LLM_model,
		messages=[
			system_message(chatgpt_system_prompt),
			user_message(f'{question}' + draft_prompt)
		],
		temperature = 1.0
	).choices[0].message.content
	return draft

def split_draft(draft, split_char = '\n\n'):
	# Split the draft into multiple paragraphs
	# split_char: '\n\n'
	draft_paragraphs = draft.split(split_char)
	# print(f'The draft answer has {len(draft_paragraphs)}')
	return draft_paragraphs

query_prompt = '''
I want to verify the content correctness of the given question, especially the last sentences.
Please summarize the content with the corresponding question.
This summarization will be used as a query to search with Bing search engine.
The query should be short but need to be specific to promise Bing can find related knowledge or pages.
You can also use search syntax to make the query short and clear enough for the search engine to find relevant language data.
Try to make the query as relevant as possible to the last few sentences in the content.
**IMPORTANT**
Just output the query directly. DO NOT add additional explanations or introducement in the answer unless you are asked to.
'''
def get_query(question, answer):
	query = openai.chat.completions.create(
		model=LLM_model,
		messages=[
			system_message(chatgpt_system_prompt),
			user_message(f'##Question: {question}\n\n##Content: {answer}\n\n##Instruction: {query_prompt}')
		],
		temperature = 1.0
	).choices[0].message.content
	return query

def get_content(query):
	res = get_search(query, 1)
	if not res:
		print('>>> No good Google Search Result was found')
		return None
	search_results = res[0]
	link = search_results['link'] # title, snippet
	res = get_page_content(link)
	if not res:
		print(f'>>> No content was found in {link}')
		return None
	retrieved_text = res
	trunked_texts = chunk_texts(retrieved_text, 1500)
	trunked_texts = [trunked_text.replace('\n', ' ') for trunked_text in trunked_texts]
	return trunked_texts

revise_prompt = '''
I want to revise the answer according to retrieved related text of the question in WIKI pages.
You need to check whether the answer is correct.
If you find some errors in the answer, revise the answer to make it better.
If you find some necessary details are ignored, add it to make the answer more plausible according to the related text.
If you find the answer is right and do not need to add more details, just output the original answer directly.
**IMPORTANT**
Try to keep the structure (multiple paragraphs with its subtitles) in the revised answer and make it more structual for understanding.
Split the paragraphs with `\n\n` characters.
Just output the revised answer directly. DO NOT add additional explanations or annoucement in the revised answer unless you are asked to.
'''
def get_revise_answer(question, answer, content):
	revised_answer = openai.chat.completions.create(
		model=LLM_model,
		messages=[
			system_message(chatgpt_system_prompt),
			user_message(f'##Existing Text in Wiki Web: {content}\n\n##Question: {question}\n' \
    						'\n##Answer: {answer}\n\n##Instruction: {revise_prompt}')
		],
		temperature = 1.0
	).choices[0].message.content
	return revised_answer

def get_query_wrapper(q, question, answer):
	result = get_query(question, answer)
	q.put(result)  # Put the results into the queue

def get_content_wrapper(q, query):
	try:
		result = get_content(query)
	except Exception as e:
		print(f'Error in get_content: {e}')
		result = None
	q.put(result)


def get_revise_answer_wrapper(q, question, answer, content):
	result = get_revise_answer(question, answer, content)
	q.put(result)

from multiprocessing import Process, Queue
import queue  # Needed to catch Empty exception

def run_with_timeout(func, args=(), timeout=30):
	q = Queue()  # Create a Queue object for inter-process communication
	# Create a process to execute the passed function, passing Queue and other *args, **kwargs as parameters
	p = Process(target=func, args=(q, *args))
	p.start()

	# Wait for the process to complete or time out
	try:
		# Try to get the result BEFORE joining the process
		result = q.get(timeout=timeout)
	except queue.Empty:
		print(f'{datetime.now()} [INFO] function {func.__name__} Execution timed out ({timeout}s), terminating the process...')
		p.terminate()
		p.join()
		return None
	except Exception as e:
		print(f'Exception while getting result from queue: {e}')
		p.terminate()
		p.join()  # Make sure the process is terminated
		return None  # In case of timeout, we have no results

	p.join()
	return result

from difflib import unified_diff
from IPython.display import display, HTML

def generate_diff_html(text1, text2):
	diff = unified_diff(text1.splitlines(keepends=True),
						text2.splitlines(keepends=True),
						fromfile='text1', tofile='text2')

	diff_html = ""
	for line in diff:
		if line.startswith('+'):
			diff_html += f"<div style='color:green;'>{line.rstrip()}</div>"
		elif line.startswith('-'):
			diff_html += f"<div style='color:red;'>{line.rstrip()}</div>"
		elif line.startswith('@'):
			diff_html += f"<div style='color:blue;'>{line.rstrip()}</div>"
		else:
			diff_html += f"{line.rstrip()}<br>"
	return diff_html


# RAT Function
newline_char = '\n'

def rat(question):
	print(f'{datetime.now()} [INFO] Get Draft...')
	draft = get_draft(question)
	print(f'{datetime.now()} [INFO] Fetched the Draft')
	print(f'##################### DRAFT #######################')
	print(draft)
	print(f'#####################  END  #######################')

	print(f'{datetime.now()} [INFO] Processing Drafts...')
	draft_paragraphs = split_draft(draft)
	print(f'{datetime.now()} [INFO] The draft is divided into {len(draft_paragraphs)} parts')
	answer = ''
	for i, p in enumerate(draft_paragraphs):
		print(str(i)*80)
		print(f'{datetime.now()} [INFO] Modify {i+1}/{len(draft_paragraphs)} parts...')
		answer = answer + '\n\n' + p
		# print(f'[{i}/{len(draft_paragraphs)}] Original Answer:\n{answer.replace(newline_char, ' ')}')

		# query = get_query(question, answer)
		print(f'{datetime.now()} [INFO] Generating corresponding Query...')
		res = run_with_timeout(get_query_wrapper, args=(question, answer), timeout=3)

		if not res:
			print(f'{datetime.now()} [INFO] No response. Skipping next steps...')
			continue
		else:
			query = res
		print(f'>>> {i}/{len(draft_paragraphs)} Query: {query.replace(newline_char, " ")}')

		print(f'{datetime.now()} [INFO] Get web page content...')
		# content = get_content(query)
		res = run_with_timeout(get_content_wrapper, args=(query,), timeout=5)

		if not res:
			print(f'{datetime.now()} [INFO] No response. Skipping next steps...')
			continue
		else:
			content = res

		for j, c in enumerate(content):
			if  j > 2:
				break
			print(f'{datetime.now()} [INFO] Modifying the answer according to page...[{j}/{min(len(content),3)}]')
			# answer = get_revise_answer(question, answer, c)
			res = run_with_timeout(get_revise_answer_wrapper, args=(question, answer, c), timeout=10)

			if not res:
				print(f'{datetime.now()} [INFO] No response. Skipping next steps...')
				continue
			else:
				diff_html = generate_diff_html(answer, res)
				display(HTML(diff_html))
				answer = res
			print(f'{datetime.now()} [INFO] Answer updation completed: [{j}/{min(len(content),3)}]')
		# print(f'[{i}/{len(draft_paragraphs)}] REVISED ANSWER:\n {answer.replace(newline_char, ' ')}')
		# print()
	return draft, answer

# draft, answer = rat("Introduce Jin-Yong's Life.")

# diff_html = generate_diff_html(draft, answer)
# display(HTML(diff_html))
