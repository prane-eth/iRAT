# Orchestrates the end-to-end iRAT flow

from irat.utils.logger import log_debug, log_error, log_info
from irat.utils.prompt_security import is_safe, UnsafePromptError

from irat.draft_revision import revise_draft, revise_using_feedback
from irat.initial_drafting import generate_initial_draft
from irat.reflection_replanning import get_evaluator_feedback
from irat.retrieval import is_uncertain, reset_budget

import time
from typing import List, Tuple


def run_pipeline(user_query: str, initial_draft: str = None) -> Tuple[str, List[str], str]:
	# Run the iRAT pipeline with the given user question.

	reset_budget()  # The budget limit is for only 1 query.

	# Prompt safety check
	if not is_safe(user_query):
		log_info('Unsafe prompt:', user_query[:50], '...')
		raise UnsafePromptError(user_query)

	# Get initial response from LLM
	log_info('Generating draft v1...')
	all_revisions = []
	if not initial_draft:
		initial_draft = generate_initial_draft(user_query)

	# Uncertainty estimation
	if is_uncertain(user_query, initial_draft, uncertainty_threshold=0.3):
		log_info('Generating draft v2...')
		_, revised_draft = revise_draft(initial_draft, user_query)
	else:
		revised_draft = initial_draft

	# Get a feedback from the Chain Evaluator
	log_info('Replanning: Analyzing the thoughts...')
	evaluator_feedback = get_evaluator_feedback(user_query, initial_draft, revised_draft)

	# Final response generation:
	# Revise the draft using evaluator feedback
	log_info('Generating draft v3...')
	final_answer = revise_using_feedback(revised_draft, user_query, evaluator_feedback)

	return initial_draft, revised_draft, evaluator_feedback, final_answer


log_debug('Pipeline loaded successfully.')


if __name__ == '__main__':
	# Example usage
	user_query = 'What is the capital of France?'
	start_time = time.time()
	try:
		_, _, _, draft_3 = run_pipeline(user_query)
		log_info(f'Final Draft: {draft_3}')
	except UnsafePromptError as e:
		log_error(e)
	total_time = time.time() - start_time
	log_info(f'Total Time Taken: {total_time:.2f} seconds')
