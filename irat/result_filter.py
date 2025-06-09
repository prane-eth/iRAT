# Result filtering module

# from .lm_adapter import get_response
from irat.utils.attention_retrieval import get_selected_indices
from .utils.domain_filter import filter_urls
from .utils.page_parser import get_page_contents
from .stage_base import StageBase

"""
Filtering raw search results using spam filtering and "Attention-Retrieval" method
"""


class ResultFilter(StageBase):
    STAGE = "result_filter"

    def __init__(self, model_name: str = None):
        
        pass

    def score_snippet(self, question: str, snippet: str) -> float:
        
        pass

    def filter_results(self, question: str, raw_snippets: list[str],
                        threshold: float = 0.5, urls: list[str] = []) -> list[str]:
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

        # return contents at those indices
        filtered_snippets = [contents[i] for i in selected_indices if i < len(contents)]
        if not filtered_snippets:
            raise ValueError('No valid snippets found after filtering.')
        return filtered_snippets

def filter_results(raw_snippets: list[str], question: str = "",
                    urls: list[str] = []) -> list[str]:
    """
    Top-level helper that instantiates ResultFilter and calls its filter_results().
    """
    rf = ResultFilter()
    return rf.filter_results(question=question, raw_snippets=raw_snippets, urls=urls)
