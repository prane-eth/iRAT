from irat.uncertainty import Uncertainty
from irat.budget_control import BudgetControl
from irat.stage_base import StageBase

# initial draft of function. more changes to be made
class Retrieval(StageBase):
    STAGE = "retrieval"

    def __init__(self, budget: BudgetControl, uncertainty_threshold: float = 0.3):
        self.budget               = budget
        self.uncertainty_threshold = uncertainty_threshold

    def should_retrieve(self, question: str, draft: str = None) -> bool:
        # 1) Budget must allow
        if not self.budget.can_retrieve():
            return False

        # 2) Compute model uncertainty
        score = Uncertainty.compute_uncertainty_for_question(question, num_samples=3, draft=draft)
        # Retrieve only if uncertainty is above threshold
        return score >= self.uncertainty_threshold

    def retrieve(self, question: str, draft: str) -> List[Snippet]:
        if self.should_retrieve(question, draft):
            self.budget.record_retrieval()
            # form query from draft+question, call search, etc.
            return self.call_search_api(question, draft)
        else:
            return []
