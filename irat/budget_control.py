# budget_control.py

from .stage_base import StageBase

"""
Budget tracking for multiple retrievals
"""

class BudgetControl(StageBase):
    STAGE = "budget_control"

    # intitial code
    def __init__(self, max_retrievals: int = 3):
        self.max_retrievals = max_retrievals
        self.used = 0

    def can_retrieve(self) -> bool:
        return self.used < self.max_retrievals

    def record_retrieval(self):
        if not self.can_retrieve():
            raise RuntimeError("Retrieval budget exhausted.")
        self.used += 1

    def reset(self):
        self.used = 0
