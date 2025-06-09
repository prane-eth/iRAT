# pipeline.py

from irat.stage_base import StageBase
from irat.lm_adapter import LMAdapter
# from .uncertainty import Uncertainty
from irat.budget_control import BudgetControl
from irat.retrieval import Retrieval
from irat.draft_revision import DraftRevision
from .reflection_replanning import ReflectionReplanning
from .dynamic_prompt import DynamicPrompt

"""
Orchestrates the end-to-end iRAT flow
"""

class Pipeline(StageBase):
    STAGE = "pipeline"

    def __init__(self, use_openai: bool = True):
        
        pass

    def run(self, user_question: str) -> str:
        
        pass



# if __name__ == "__main__":
#     # Example usage stub
#     pipeline = Pipeline(use_openai=True)
#     question = "What is the capital of France?"
#     answer = pipeline.run(question)
#     print("\n--- iRAT Final Answer ---\n")
#     print(answer)
