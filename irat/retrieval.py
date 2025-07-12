from __future__ import annotations
from typing import List
from irat.uncertainty import Uncertainty
from irat.utils.google_search import GoogleSearch
from irat.utils.logger import log_info

google_searcher = GoogleSearch()

# ────────────────────── Budget controller ──────────────────────

# Less budget, but the "used" count should be reset for every query.
max_retrievals = 30

def get_used_retrievals() -> int:
	# Read the budget from a file, if it exists.
	try:
		with open('budget_used.txt') as f:
			return int(f.read().strip())
	except:
		return 0

def write_budget_file(budget: int) -> None:
	# Write the budget to a file.
	with open('budget_used.txt', 'w') as f:
		f.write(str(budget))

def is_budget_available(used: int = None) -> bool:
	if used is None:  # If not provided, get the value.
		used = get_used_retrievals()
	return used < max_retrievals

def record_retrieval(avoid_error=False) -> None:
	used = get_used_retrievals() + 1
	write_budget_file(used)
 
	if not avoid_error and not is_budget_available(used):
		raise RuntimeError('Retrieval budget exhausted.')

def reset_budget() -> None:
	# Alias to reset the retrieval budget.
	write_budget_file(0)


# ────────────────────── Uncertainty gate ───────────────────────
def is_uncertain(
	question: str,
	draft: str | None = None,
	uncertainty_threshold: float = 0.30,
) -> bool:
	"""
	Return True if uncertainty score exceeds threshold and budget remains.
	"""
	if not is_budget_available():
		log_info("Retrieval budget exhausted.")
		return False
	score = Uncertainty.compute_uncertainty_for_question(question, draft=draft)
	return score >= uncertainty_threshold

# ────────────────────── Retrieval logic ────────────────────────
unsupported_strings = (
	# Unsupported URLs
	"youtube.com", "/pdf", "bing.com", "arxiv.org/html", 
	# Files
	'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.json', '.csv', 
	# Datasets should not be used for answers
	"humaneval", "human-eval", "human_eval", "mbpp", "gsm8k"
)
def retrieve(question: str) -> List[str]:
	"""
	Run Google search if `force` or if `is_uncertain` passes.
	Returns a *deduplicated* list of clean URLs.
	"""
	record_retrieval()
	urls = google_searcher.run_query(question)
	urls = [u for u in urls if all(b not in u.lower() for b in unsupported_strings)]
	return list(set(urls))


if __name__ == "__main__":
	# Example usage
	question = "What is the capital of France?"
	draft = "The capital of France is"
	reset_budget()  # Reset budget for this example
	retrieved_urls = retrieve(question)
	print("Retrieved URLs:", retrieved_urls)
	print("Used retrievals:", get_used_retrievals())
