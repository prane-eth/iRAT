# Result filtering module to filter search results using spam filtering and Attention-Retrieval

from irat.utils.attention_retrieval import get_selected_indices
from irat.utils.domain_filter import filter_urls
from irat.utils.page_load_and_parse import get_page_contents
# from irat.stage_base import StageBase

# class ResultFilter(StageBase):
# 	STAGE = "result_filter"
# 	def __init__(self):
# 		pass
# 	def score_snippet(self, question: str, snippet: str) -> float:
# 		pass
# 	def filter_results(self, question: str, raw_snippets: list[str],
# 						threshold: float = 0.5, urls: list[str] = []) -> list[str]:
# 		pass


def fetch_and_filter_results(question: str, urls: list[str]) -> list[str]:
	if not urls:
		raise ValueError('No URLs provided for filtering.')
	filtered_urls = filter_urls(urls)  # remove suspicious URLs
	if not filtered_urls:
		raise ValueError('No valid URLs found after filtering.')
	contents = get_page_contents(filtered_urls)  # get contents of the pages
	if not contents:
		raise ValueError('No valid page contents found for filtering.')

	# apply attention-retrieval method
	selected_indices = get_selected_indices(question, contents)
	if not selected_indices:
		raise ValueError('No valid indices selected for filtering.')
	# return contents at the selected indices
	filtered_snippets = [contents[i] for i in selected_indices if i < len(contents)]
	if not filtered_snippets:
		raise ValueError('No valid snippets found after filtering.')
	return filtered_snippets

