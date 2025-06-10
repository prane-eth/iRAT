# Wraps OpenAI/Transformers calls for “initial draft”
from irat.stage_base import StageBase
from irat.utils.common_functions import user_message
from irat.utils.settings import env
from openai import OpenAI

default_model = env('LLM_NAME')
client = OpenAI()

def get_response(prompt: str, model: str = default_model) -> str:
    """
    Helper function to get a response from the OpenAI API.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[user_message(prompt)],
    )
    return response.choices[0].message['content'].strip()


class LMAdapter(StageBase):
    STAGE = "lm_adapter"

    def __init__(self):
        pass

    def generate_initial_draft(self, user_query: str) -> str:
        return get_response(user_query)

    def generate_revision(self, prompt: str) -> str:
        pass
