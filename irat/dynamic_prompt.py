# dynamic_prompt.py

from irat.utils.stage_base import StageBase

"""
Dynamic‐prompt adaptation (fallback to RL later)
"""

class DynamicPrompt(StageBase):
    STAGE = "dynamic_prompt"

    def __init__(self):
       
        pass

    def adapt(self, draft: str, domain: str = None) -> str:
        
        pass
