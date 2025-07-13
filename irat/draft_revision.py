# Draft revision using retrieved text

from irat.utils.lm_functions import get_response, split_draft
from irat.utils.logger import log_debug, log_error, log_info

from irat.result_filter import fetch_and_filter_results
from irat.retrieval import retrieve  # , GOOGLE_API_KEYS

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
		log_info(f'Error: function {func.__name__} Execution timed out ({timeout}s), terminating the process...')
		p.terminate()
		p.join()
		return None
	except Exception as e:
		log_error(f'Exception while getting result from queue: {e}')
		p.terminate()
		p.join()  # Make sure the process is terminated
		return None  # In case of timeout, we have no results

	p.join()
	return result


QUERY_PROMPT = '''
I want to verify the content correctness of the given question, especially the last sentences.
Please summarize the content with the corresponding question.
This summarization will be used as a query to search with Bing search engine.
The query should be short but need to be specific to promise Bing can find related knowledge or pages.
You can also use search syntax to make the query short and clear enough for the search engine to find relevant language data.
Try to make the query as relevant as possible to the last few sentences in the content.
**IMPORTANT**
Just output the query directly. DO NOT add additional explanations or introducement in the answer unless you are asked to.
'''

REVISE_PROMPT = '''
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

def get_query(question, answer):
	return get_response(
		f'##Question: {question}\n\n##Content: {answer}\n\n##Instruction: {QUERY_PROMPT}'
	)

def get_query_wrapper(q, question, answer):
	result = get_query(question, answer)
	q.put(result)  # Put the results into the queue


URL_RESULT_LIMIT = 4  # 3 is good, but some spam URLs get filtered.
URLS_AFTER_FILTERING = 1  # Use only 1 after filtering.

def get_content_wrapper(q, query):
	try:
		retrieved_URLs = retrieve(query)
		if not retrieved_URLs:
			log_info('No relevant URLs retrieved for the query.')
			result_paragraphs = []
			q.put(result_paragraphs)
			return

		log_info('Filtering retrieved results...')
		urls = retrieved_URLs[:URL_RESULT_LIMIT]
		result_paragraphs = fetch_and_filter_results(query, urls, limit=URLS_AFTER_FILTERING)
		log_info('Filtered paragraphs:', len(result_paragraphs))

	except Exception as e:
		if '429' in str(e):
			log_error('Google API rate limit exceeded.')
			raise e
		elif 'Safe Browsing API has not been used' in str(e):
			log_error('Safe Browsing API has not been used')
			raise e
		else:
			log_error(f'Error in get_content:', str(e).split('key=')[0])
		result_paragraphs = None
	q.put(result_paragraphs)


def get_revise_answer(question: str, answer: str, paragraph: str) -> str:
	return get_response(
		f'## Existing Text in Wiki Web: {paragraph}\n\n## Question: {question}\n' \
			f'\n## Answer: {answer}\n\n## Instruction: {REVISE_PROMPT}'
	)

def get_revise_answer_wrapper(q, question: str, answer: str, content: str):
	result = get_revise_answer(question, answer, content)
	q.put(result)


def revise_draft(draft: str, user_query: str) -> str:
	log_info('Processing Drafts...')
	draft_paragraphs = split_draft(draft)
	log_info(f'The draft is divided into {len(draft_paragraphs)} parts')
	answer = ''
	all_revisions = []  # to return later

	for i, p in enumerate(draft_paragraphs):
		log_debug('-'*10)
		log_info(f'Modify {i+1}/{len(draft_paragraphs)} parts...')
		answer = answer + '\n\n' + p

		log_info('Generating corresponding Query...')
		res = run_with_timeout(get_query_wrapper, args=(user_query, answer), timeout=30)

		if not res:
			log_info('No response. Skipping next steps...')
			continue
		else:
			query = res
		log_debug(f'>>> {i}/{len(draft_paragraphs)} Query:', query.replace('\n', ' '))

		log_info('Get web page content...')
		search_res_paragraphs = run_with_timeout(get_content_wrapper, args=(query, ), timeout=45)
		if not search_res_paragraphs:
			log_info('No response. Skipping next steps...')
			continue

		all_revisions.append(f'Query: {query}')
		used_contents = []
		for c_index, content in enumerate(search_res_paragraphs):  # use each result to edit the answer
			if len(used_contents) >= 2:
				break
			log_info(f'Modifying the answer according to page...[{c_index+1}/{min(len(search_res_paragraphs),3)}]')
			res = run_with_timeout(get_revise_answer_wrapper, args=(user_query, answer, content), timeout=30)

			if not res:
				log_info('No response. Skipping next steps...')
				continue
			else:
				answer = res
				used_contents.append(c_index)
			all_revisions.append(answer)
	return all_revisions, answer.strip()


def revise_using_feedback(draft: str, user_query: str, feedback: str) -> str:
	prompt = (
		f'User Query: {user_query} \n'
		f'Draft: {draft} \n'
		' --- \n'
		f'Feedback on your draft: {feedback} \n'
		' --- \n'
		'Revise the draft based on the feedback and user query: \n'
		f'Reminding again about the user query: {user_query} \n'
		' --- \n'
		'Respond to the user directly. Don\'t mention that I provided additional information. \n'
	)
	return get_response(prompt)


# Reference: https://github.com/CraftJarvis/RAT/blob/main/creative.ipynb


if __name__ == '__main__':
	# Example usage
	query = 'What is OpenAI?'
	answer = 'OpenAI is an AI research and deployment company.'
	content = 'OpenAI has developed several AI models, including GPT-3.'
	result = get_revise_answer(query, answer, content)
	log_debug('Revised Answer:', result.strip())
 
	initial_draft = 'As an AI language model, I do not have access to real-time information'
	retrieved_passages = [
		'OpenAI is an AI research and deployment company.',
		'OpenAI has developed several AI models, including GPT-3.',
		'GPT-3 is known for its ability to generate human-like text.',
	]
	user_query = 'What is OpenAI?'
	draft_2, revised_response = revise_draft(initial_draft, user_query)
	log_debug('Revised Response:', revised_response.strip())
	log_debug('New draft:', draft_2)