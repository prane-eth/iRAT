# Orchestrates the end-to-end iRAT flow

from irat.lm_adapter import LMAdapter
from irat.uncertainty import Uncertainty
from irat.retrieval import Retrieval
from irat.draft_revision import DraftRevision
from irat.reflection_replanning import ReflectionReplanning
from irat.dynamic_prompt import DynamicPrompt
from irat.result_filter import fetch_and_filter_results
from irat.utils.logger import log_debug, log_info
# from irat.stage_base import StageBase

# class Pipeline(StageBase):
# 	STAGE = "pipeline"
# 	def __init__(self, use_openai: bool = True):
# 		pass
# 	def run(self, user_question: str) -> str:
# 		pass

# Stages of the pipeline
uncertainty = Uncertainty()
retrieval = Retrieval()
draft_revision = DraftRevision()
reflection_replanning = ReflectionReplanning()
dynamic_prompt = DynamicPrompt()
lm_adapter = LMAdapter()


def run_pipeline(user_question: str) -> str:
	# Run the iRAT pipeline with the given user question.

	# Get initial response from LM
	log_info('Generating first draft response...')
	first_draft = lm_adapter.generate_initial_draft(user_question)

	# Retrieval decision
	# includes uncertainty estimation and budget control
	log_info('Attempting retrieval...')
	retrieved_URLs = retrieval.retrieve(user_question, first_draft, force=True)
	log_debug('Retrieved URLs:', retrieved_URLs)
	result_paragraphs = []
	if retrieved_URLs:
		retrieved_URLs = retrieved_URLs[:5]  # use only top 5 URLs

		# Result filter
		log_info('Filtering retrieved results...')
		result_paragraphs = fetch_and_filter_results(user_question, retrieved_URLs,
                                               			top_k=10, score_threshold=1.5)
		log_debug('Filtered:', result_paragraphs, '\n\n')

		if result_paragraphs:
			# Draft a revised response
			revised_response = draft_revision.revise(first_draft, result_paragraphs, user_question)
			# log_debug('Revised Response:', revised_response)

			# Temporarily return the revised response for testing
			return revised_response

	# Reflection and replanning
	# ...
	# Dynamic prompting
	# ...
	# Final response generation
	# ...
	# return final_response.strip() or 'Error generating response.'



if __name__ == '__main__':
	# Example usage
	# query = 'What is the latest version of LangChain package.'
	query = 'How to get LLM response from latest version of LangChain?'
	answer = run_pipeline(query)
	print('\n--- iRAT Final Answer ---\n')
	print(answer)
