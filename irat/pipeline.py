# Orchestrates the end-to-end iRAT flow

from irat.lm_adapter import get_response
from irat.uncertainty import Uncertainty
from irat.budget_control import BudgetControl
from irat.retrieval import Retrieval
from irat.draft_revision import DraftRevision
from irat.reflection_replanning import ReflectionReplanning
from irat.dynamic_prompt import DynamicPrompt
from irat.result_filter import fetch_and_filter_results
from irat.utils.logger import log_info
# from irat.stage_base import StageBase

# class Pipeline(StageBase):
# 	STAGE = "pipeline"
# 	def __init__(self, use_openai: bool = True):
# 		pass
# 	def run(self, user_question: str) -> str:
# 		pass

# Stages of the pipeline
uncertainty = Uncertainty()
budget_control = BudgetControl()
retrieval = Retrieval()
draft_revision = DraftRevision()
reflection_replanning = ReflectionReplanning()
dynamic_prompt = DynamicPrompt()


def run_pipeline(user_question: str) -> str:
	# Run the iRAT pipeline with the given user question.

	# Get initial response from LM
	log_info('Generating first draft response...')
	first_draft = get_response(user_question)

	# Retrieval decision
	# includes uncertainty estimation and budget control
	log_info('Attempting retrieval...')
	retrieved_URLs = retrieval.retrieve(user_question, first_draft)
	if retrieved_URLs:
		# Result filter
		log_info('Filtering retrieved results...')
		result_paragraphs = fetch_and_filter_results(retrieved_URLs)
		return result_paragraphs

		if result_paragraphs:
			# Draft a revised response
			revised_response = draft_revision.revise(first_draft, result_paragraphs, user_question)

	# Reflection and replanning
	# ...
	# Dynamic prompting
	# ...
	# Final response generation
	# ...
	# return final_response



if __name__ == '__main__':
	# Example usage
	answer = run_pipeline('Tell me about latest events at the University of Arizona.')
	print('\n--- iRAT Final Answer ---\n')
	print(answer)
