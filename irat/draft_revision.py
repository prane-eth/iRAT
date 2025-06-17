# Draft revision using retrieved text

from irat.result_filter import fetch_and_filter_results
from irat.retrieval import retrieve
from irat.utils.common_functions import run_with_timeout
from irat.utils.lm_functions import get_response, split_draft
from irat.utils.logger import log_debug, log_info

draft_prompt = '''
IMPORTANT:
Try to answer this question/instruction with step-by-step thoughts and make the answer more structural.
Use `\n\n` to split the answer into several paragraphs.
Just respond to the instruction directly. DO NOT add additional explanations or introducement in the answer unless you are asked to.
'''

def generate_initial_draft(user_query: str) -> str:
	draft = get_response(user_query + draft_prompt)
	log_info('Fetched the Draft')
	draft_paragraphs = split_draft(draft)
	# log_info(f'The draft is divided into {len(draft_paragraphs)} parts')
	return draft_paragraphs, draft



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
	return get_response(
		f'##Question: {question}\n\n##Content: {answer}\n\n##Instruction: {query_prompt}'
	)

def get_query_wrapper(q, question, answer):
	result = get_query(question, answer)
	q.put(result)  # Put the results into the queue

def get_content_wrapper(q, query):
	try:
		retrieved_URLs = retrieve(query, draft=None, force=True)
		retrieved_URLs = retrieved_URLs[:5]  # use only top 5 URLs
		log_info('Filtering retrieved results...')
		result_paragraphs = fetch_and_filter_results(query, retrieved_URLs)
		log_debug('Filtered:', result_paragraphs, '\n\n')
	except Exception as e:
		log_debug(f'Error in get_content: {e}')
		result_paragraphs = None
	q.put(result_paragraphs)



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
def get_revise_answer(question: str, answer: str, content: str) -> str:
	revised_answer = get_response(
		(f'##Existing Text in Wiki Web: {content}\n\n##Question: {question}\n' \
			f'\n##Answer: {answer}\n\n##Instruction: {revise_prompt}')
	)
	return revised_answer

def get_revise_answer_wrapper(q, question: str, answer: str, content: str):
	result = get_revise_answer(question, answer, content)
	q.put(result)


newline_char = '\n'

def revise_draft(draft: str, user_query: str) -> str:
	log_info('Processing Drafts...')
	draft_paragraphs = split_draft(draft)
	log_info(f'The draft is divided into {len(draft_paragraphs)} parts')
	answer = ''
	for i, p in enumerate(draft_paragraphs):
		log_debug('-'*10 + f' - {i} - '*10 + '-'*10)
		log_info(f'Modify {i+1}/{len(draft_paragraphs)} parts...')
		answer = answer + '\n\n' + p
		# log_debug(f'[{i}/{len(draft_paragraphs)}] Original Answer:\n{answer.replace(newline_char, ' ')}')

		# query = get_query(question, answer)
		log_info('Generating corresponding Query...')
		res = run_with_timeout(get_query_wrapper, args=(user_query, answer), timeout=3)

		if not res:
			log_info('No response. Skipping next steps...')
			continue
		else:
			query = res
		log_debug(f'>>> {i}/{len(draft_paragraphs)} Query: {query.replace(newline_char, " ")}')

		log_info('Get web page content...')
		# content = get_content(query)
		search_result = run_with_timeout(get_content_wrapper, args=(query,), timeout=5)
		if not search_result:
			log_info('No response. Skipping next steps...')
			continue

		for c_index, cont in enumerate(search_result):
			if  c_index > 2:
				break
			log_info(f'Modifying the answer according to page...[{c_index}/{min(len(search_result),3)}]')
			# answer = get_revise_answer(question, answer, c)
			res = run_with_timeout(get_revise_answer_wrapper, args=(user_query, answer, cont), timeout=10)

			if not res:
				log_info('No response. Skipping next steps...')
				continue
			else:
				# diff_html = generate_diff_html(answer, res) # display the differences
				# display(HTML(diff_html))
				answer = res
			log_info(f'Answer updation completed: [{c_index}/{min(len(search_result),3)}]')
		# log_debug(f'[{i}/{len(draft_paragraphs)}] REVISED ANSWER:\n {answer.replace(newline_char, ' ')}')
		# log_debug()
	return draft, answer





# def revise_draft(draft: str, retrieved_passages: list[str], user_query: str) -> str:
# 	prompt = (
# 		'\n'.join(retrieved_passages) + '\n\n'
# 		' --- \n'
# 		f'Draft: {draft} \n'
# 		' --- \n'
# 		'Revise the draft based on the additional information and user query: \n'
# 		f'User Query: {user_query} \n'
# 		' --- \n'
# 		'Do not mention that I provided you with additional information. \n'
# 	)
# 	# log_debug('Draft Revision Prompt:', prompt, '\n\n')
# 	return get_response(prompt)


if __name__ == '__main__':
	# Example usage
	initial_draft = 'As an AI language model, I do not have access to real-time information'
	retrieved_passages = [
		'OpenAI is an AI research and deployment company.',
		'OpenAI has developed several AI models, including GPT-3.',
		'GPT-3 is known for its ability to generate human-like text.',
	]
	user_query = 'What is OpenAI?'
	draft_2, revised_response = revise_draft(initial_draft, retrieved_passages, user_query)
	log_debug('Revised Response:', revised_response.strip())
	log_debug('New draft:', draft_2)