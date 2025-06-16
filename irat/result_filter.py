# Result filtering module to filter search results using spam filtering and Attention-Retrieval

from irat.utils.attention_retrieval import select_paragraphs
from irat.utils.domain_filter import filter_urls
from irat.utils.logger import log_debug
from irat.utils.page_load_and_parse import get_page_contents
# from irat.stage_base import StageBase

# class ResultFilter(StageBase):
# 	STAGE = 'result_filter'
# 	def __init__(self):
# 		pass
# 	def score_snippet(self, question: str, snippet: str) -> float:
# 		pass
# 	def filter_results(self, question: str, raw_snippets: list[str],
# 						threshold: float = 0.5, urls: list[str] = []) -> list[str]:
# 		pass


def fetch_and_filter_results(question: str, urls: list[str], top_k: int, 
                             score_threshold: float) -> list[str]:
	if not urls:
		raise ValueError('No URLs provided for filtering.')

	filtered_urls = filter_urls(urls)  # remove suspicious URLs
	# log_debug('Filtered URLs:', filtered_urls)
	if not filtered_urls:
		raise ValueError('No valid URLs found after filtering.')

	contents, paragraphs_list = get_page_contents(filtered_urls)  # get contents of the pages
	# log_debug('Page Contents:', contents)
	if not contents:
		raise ValueError('No valid page contents found for filtering.')

	# apply attention-retrieval method
	selected_paragraphs = select_paragraphs(question, contents, top_k, score_threshold)

	# log_debug('Selected Paragraphs:', selected_paragraphs)
	if not selected_paragraphs:
		raise ValueError('No paragraphs selected after filtering.')

	return selected_paragraphs


if __name__ == '__main__':
	# Example usage
	question = 'What is the capital of France?'
	urls = ['https://en.wikipedia.org/wiki/Paris', 'https://www.bbc.com/news/world-europe-17298730']
	try:
		results = fetch_and_filter_results(question, urls)
		print('Filtered Results:', results)
	except ValueError as e:
		print('Error:', e)
