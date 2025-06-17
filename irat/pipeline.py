# Orchestrates the end-to-end iRAT flow

from irat.uncertainty import Uncertainty
from irat.retrieval import is_uncertain, retrieve
from irat.draft_revision import generate_initial_draft, revise_draft
from irat.reflection_replanning import ReflectionReplanning
from irat.dynamic_prompt import DynamicPrompt
from irat.result_filter import fetch_and_filter_results
from irat.utils.logger import log_debug, log_info

# Stages of the pipeline
uncertainty = Uncertainty()
reflection_replanning = ReflectionReplanning()
dynamic_prompt = DynamicPrompt()


def run_pipeline(user_question: str) -> str:
	# Run the iRAT pipeline with the given user question.

	all_drafts = []

	# Get initial response from LM
	log_info('Generating first draft response...')
	_, initial_draft = generate_initial_draft(user_question)
	all_drafts.append(initial_draft)

	# Uncertainty estimation
	# if is_uncertain(user_question, initial_draft):  # Skip for now. Add later.
	thoughts, revised_response = revise_draft(initial_draft, user_question)
	return thoughts.strip(), revised_response.strip()

	# # Retrieval decision
	# # includes uncertainty estimation and budget control
	# log_info('Attempting retrieval...')
	# retrieved_URLs = retrieve(user_question, initial_draft, force=True)
	# log_debug('Retrieved URLs:', retrieved_URLs)
	# result_paragraphs = []
	# if retrieved_URLs:
	# 	retrieved_URLs = retrieved_URLs[:5]  # use only top 5 URLs
	# 	# Result filter
	# 	log_info('Filtering retrieved results...')
	# 	result_paragraphs = fetch_and_filter_results(user_question, retrieved_URLs)
	# 	log_debug('Filtered:', result_paragraphs, '\n\n')

	# 	if result_paragraphs:
	# 		# Draft a revised response
	# 		revised_response = revise_draft(initial_draft, result_paragraphs, user_question)
	# 		all_drafts.append(revised_response)
	# 		# log_debug('Revised Response:', revised_response)

	# 		# Temporarily return the revised response for testing
	# 		return all_drafts[-2], revised_response

	# Reflection and replanning
	# ...
	# Dynamic prompting
	# ...
	# Final response generation
	# ...
	# return final_response.strip() or 'Error generating response.'

	# return 'No relevant information found. Please try again.'



if __name__ == '__main__':
	# Example usage
	# query = 'What is the latest version of LangChain package.'
	query = 'How to get LLM response from latest version of LangChain?'
	thoughts, answer = run_pipeline(query)
	log_debug('\n--- iRAT Final Answer ---\n')
	log_debug(answer)
	log_debug('\n--- iRAT Thoughts ---\n')
	log_debug(thoughts)
