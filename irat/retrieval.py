# retrieval.py

from .stage_base import StageBase

"""
Conditional retrieval decision & budget control
"""

class Retrieval(StageBase):
    STAGE = "retrieval"

    def __init__(self, budget_controller, uncertainty_threshold: float = 0.3):
        # … (existing init logic) …
        pass

    def should_retrieve(self, uncertainty_score: float) -> bool:
        # … (existing code) …
        pass

    def form_search_query(self, user_query: str, draft: str) -> str:
        # … (existing code) …
        pass

    def call_search_api(self, query: str, top_k: int = 5) -> list[str]:
        # … (existing code) …
        pass

    def retrieve(self, user_query: str, draft: str) -> list[str]:
        # … (existing code) …
        pass
