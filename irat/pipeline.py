# Orchestrates the end-to-end iRAT flow

from irat.utils.logger import log_debug, log_error, log_info
from irat.utils.prompt_security import is_safe, UnsafePromptError
from irat.draft_revision import revise_draft, revise_using_feedback
from irat.initial_drafting import generate_initial_draft
from irat.reflection_replanning import get_evaluator_feedback
from irat.retrieval import is_uncertain

import time
from typing import List, Tuple


def run_pipeline(user_query: str, draft_1: str = None) -> Tuple[str, List[str], str]:
	# Run the iRAT pipeline with the given user question.

	# Prompt safety check
	if not is_safe(user_query):
		log_info('Unsafe prompt:', user_query[:50], '...')
		raise UnsafePromptError(user_query)

	# Get initial response from LM
	log_info('Generating draft v1...')
	all_revisions = []
	# Short responses lack reasoning and should be re-generated.
	# Handling short responses is the limitation not handled by old-RAT.
	if not draft_1 or len(draft_1) < 120:
		draft_1 = generate_initial_draft(user_query)
	all_revisions.append(draft_1)

	# Uncertainty estimation
	if is_uncertain(user_query, draft_1, uncertainty_threshold=0.01):
		log_info('Generating draft v2...')
		new_revisions, draft_2 = revise_draft(draft_1, user_query)
		# Short responses lack reasoning
		if len(draft_2) < 120:
			new_revisions, draft_2 = revise_draft(draft_1, user_query)
		if new_revisions:
			all_revisions.append(new_revisions)
	else:
		# If no uncertainty, we can skip the rest of the pipeline.
		# No revisions needed, return initial draft only.
		draft_2 = draft_1

	# Using feedback directly without sentiment analysis of the feedback.
	log_info('Replanning: Analyzing the thoughts...')
	evaluator_feedback = get_evaluator_feedback(user_query, draft_1, draft_2)
	if len(evaluator_feedback) < 10:
		evaluator_feedback = get_evaluator_feedback(user_query, draft_1, draft_2)
	all_revisions.append(evaluator_feedback)

	# Final response generation
	log_info('Generating draft v3...')
	draft_3 = revise_using_feedback(draft_2, user_query, evaluator_feedback)
	# Short responses lack reasoning
	if len(draft_3) < 120:
		log_info('draft_3 is too short. Trying again...')
		draft_3 = revise_using_feedback(draft_2, user_query, evaluator_feedback)
	all_revisions.append(draft_3)

	return draft_1, draft_2, all_revisions, evaluator_feedback, draft_3


log_debug('Pipeline loaded successfully.')


if __name__ == '__main__':
	# Example usage
	user_query = 'What is the capital of France?'
	start_time = time.time()
	try:
		result = run_pipeline(user_query)
		_, _, _, _, draft_3 = result
		log_info(f'Final Draft: {draft_3}')
	except UnsafePromptError as e:
		log_error(e)
	total_time = time.time() - start_time
	log_info(f'Total Time Taken: {total_time:.2f} seconds')
