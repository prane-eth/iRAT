# Result filtering module to filter search results using spam filtering and Attention-Retrieval

from irat.utils.attention_retrieval import select_paragraphs
from irat.utils.domain_filter import filter_urls
from irat.utils.lm_functions import chunk_texts
from irat.utils.logger import log_debug, log_error
from irat.utils.page_load_and_parse import get_page_contents

def fetch_and_filter_results(question: str, urls: list[str]) -> list[str]:
	if not urls:
		raise ValueError('No URLs provided for filtering.')

	filtered_urls = filter_urls(urls)  # remove suspicious URLs
	# log_debug('Filtered URLs:', filtered_urls)
	if not filtered_urls:
		raise ValueError('No valid URLs found after filtering.')

	contents = get_page_contents(filtered_urls)  # get contents of the pages
	# log_debug('Page Contents:', contents)
	if not contents:
		raise ValueError('No valid page contents found for filtering.')

	# Divide each page into chunks
	chunks = []
	for page_content in contents:
		chunks += chunk_texts(page_content, chunk_size=370)

	# apply attention-retrieval method
	selected_paragraphs = select_paragraphs(question, chunks, top_k=10, score_threshold=1.0)
 	# 	- top_k can be high because many paragraphs are in each page.
	# 	- score_threshold is low because chunks are small and get lesser scores.
	# log_debug('Selected Paragraphs:', selected_paragraphs)
	if not selected_paragraphs:
		raise ValueError('No paragraphs selected after filtering.')

	return selected_paragraphs


if __name__ == '__main__':
	# Example usage
	# question = 'What is the capital of France?'
	# urls = ['https://en.wikipedia.org/wiki/Paris', 'https://www.bbc.com/news/world-europe-17298730']
	question = 'What is the first repeated character in a given string?'
	urls = ['https://stackoverflow.com/questions/50976511/code-to-output-the-first-repeated-character-in-given-string']
	try:
		results = fetch_and_filter_results(question, urls)
		log_debug('Filtered Results:', len(results))
		# for result in results[:1]:
		# 	log_debug(result)
	except ValueError as e:
		log_error('Error:', e)
