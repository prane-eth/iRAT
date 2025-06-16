# Wraps OpenAI/Transformers calls for “initial draft”
from irat.stage_base import StageBase
from irat.utils.common_functions import user_message
from irat.utils.settings import env
from openai import OpenAI
import datetime

default_model = env('LLM_NAME')
client = OpenAI()

knowledge_cutoff = env('LLM_KNOWLEDGE_CUTOFF')

def get_date():
	return datetime.datetime.now().strftime('%Y-%m-%d')

def get_response(prompt: str, model: str = default_model) -> str:
	# Get a response through OpenAI package.
	response = client.chat.completions.create(
		model=model,
		messages=[user_message(prompt)],
	)
	return response.choices[0].message.content.strip()


def get_cutoff_text() -> str:
	return f'Your knowledge cutoff: {knowledge_cutoff}. Current date: {get_date()}. \n'

class LMAdapter(StageBase):
	STAGE = 'lm_adapter'
	# def __init__(self):
	# 	pass

	def generate_initial_draft(self, user_query: str) -> str:
		return get_response(get_cutoff_text() + user_query)

	def generate_revision(self, prompt: str) -> str:
		return get_response(get_cutoff_text() + prompt)
