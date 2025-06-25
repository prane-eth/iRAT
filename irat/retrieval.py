from irat.uncertainty import Uncertainty
from irat.utils.logger import log_info
from irat.utils.google_search import GoogleSearch

from typing import List

google_searcher = GoogleSearch()


# Budget control for retrieval
max_retrievals = 100
used_retrievals = 0

def is_retrieval_available() -> bool:
	# Check if the retrieval budget is still available
	return used_retrievals < max_retrievals

def record_retrieval():
	global used_retrievals
	if not is_retrieval_available():
		raise RuntimeError("Retrieval budget exhausted.")
	used_retrievals += 1
# get the latest state of the used reterivals
def get_used_retrievals() -> int:
    """Return the current number of retrieval calls that have been spent."""
    return used_retrievals

def reset_budget():
	global used_retrievals
	used_retrievals = 0




uncertainty_threshold: float = 0.3

def is_uncertain(question: str, draft: str = None) -> bool:
	# Compute model uncertainty
	score = Uncertainty.compute_uncertainty_for_question(question, draft=draft)
	return score >= uncertainty_threshold

def should_retrieve(question: str, draft: str = None) -> bool:
	# 1) Budget must allow
	if not is_retrieval_available():
		log_info('Budget unavailable for retrieval.')
		return False

	# 2) Compute model uncertainty
	return is_uncertain(question, draft)

def retrieve(question: str, draft: str, force=False) -> List[str]:
	if force or should_retrieve(question, draft):
		record_retrieval()
		# form query from draft+question, call search, etc.
		return google_searcher.run_query(question)
	else:
		return []
