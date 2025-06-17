from irat.uncertainty import Uncertainty
from irat.utils.stage_base import StageBase
from irat.utils.logger import log_info
from irat.utils.google_search import GoogleSearch

from typing import List

google_searcher = GoogleSearch()

class BudgetControl(StageBase):
	STAGE = "budget_control"

	# intitial code
	def __init__(self, max_retrievals: int = 100):
		self.max_retrievals = max_retrievals
		self.used = 0

	def is_available(self) -> bool:
		# Check if the retrieval budget is still available
		return self.used < self.max_retrievals

	def record_retrieval(self):
		if not self.is_available():
			raise RuntimeError("Retrieval budget exhausted.")
		self.used += 1

	def reset_budget(self):
		self.used = 0


budget = BudgetControl()

uncertainty_threshold: float = 0.3

def is_uncertain(question: str, draft: str = None) -> bool:
	# Compute model uncertainty
	score = Uncertainty.compute_uncertainty_for_question(question, draft=draft)
	return score >= uncertainty_threshold

def should_retrieve(question: str, draft: str = None) -> bool:
	# 1) Budget must allow
	if not budget.is_available():
		log_info('Budget unavailable for retrieval.')
		return False

	# 2) Compute model uncertainty
	return is_uncertain(question, draft)

def retrieve(question: str, draft: str, force=False) -> List[str]:
	if force or should_retrieve(question, draft):
		budget.record_retrieval()
		# form query from draft+question, call search, etc.
		return google_searcher.run_query(question)
	else:
		return []
