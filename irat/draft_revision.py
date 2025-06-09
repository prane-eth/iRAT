# draft_revision.py

from .stage_base import StageBase
from .lm_adapter import LMAdapter

"""
Draft revision using retrieved text
"""

class DraftRevision(StageBase):
    STAGE = "draft_revision"

    def __init__(self, lm_adapter: LMAdapter):
        
        pass

    def revise(self, draft: str, retrieved_passages: list[str], user_query: str) -> str:
        
        pass
