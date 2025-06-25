# Orchestrates the end-to-end iRAT flow

from irat.utils.common_functions import print_separator
from irat.utils.logger import log_debug, log_error, log_info
from irat.utils.prompt_security import is_safe
from irat.utils.ratelimit_counter import ratelimit_wait, \
					wait_for_rate_limit, reset_ratelimit_wait_time

from irat.draft_revision import generate_initial_draft, revise_draft, revise_using_feedback
from irat.reflection_replanning import get_evaluator_feedback
from irat.result_filter import fetch_and_filter_results
from irat.retrieval import is_uncertain, used_retrievals, reset_budget
import time
from typing import List, Tuple


def run_pipeline(user_query: str) -> Tuple[str, List[str], str] | None:
	# Run the iRAT pipeline with the given user question.

	if not is_safe(user_query):
		log_error(f'Prompt is not safe: {user_query}, so we we are skipping it.')
		return None

	all_retrievals = []
	reset_budget()
	reset_ratelimit_wait_time()
	# Get initial response from LM
	log_info('Generating draft v1...')
	all_revisions = []
	start_time = time.time()
	_, draft_1 = generate_initial_draft(user_query)
	all_revisions.append(draft_1)
	all_retrievals.append(used_retrievals)  # Total retrievals used until now.

	# Uncertainty estimation
	# if is_uncertain(user_question, initial_draft):  # Skip for now. Add later.
	log_info('Generating draft v2...')
	new_revisions, draft_2 = revise_draft(draft_1, user_query)
	all_retrievals.append(used_retrievals)
	if draft_1 != draft_2:  # If a revision is made.
		all_revisions.append(draft_2)
	if new_revisions:
		all_revisions.append(new_revisions)

	# Using feedback directly without sentiment analysis of the feedback.
	log_info('Reflection: Analyzing the thoughts...')
	evaluator_feedback = get_evaluator_feedback(user_query, draft_1, draft_2)
	all_revisions.append(evaluator_feedback)

	# Final response generation
	log_info('Generating draft v3...')
	draft_3 = revise_using_feedback(draft_2, user_query, evaluator_feedback)
	end_time = time.time()
	all_revisions.append(draft_3)
	all_retrievals.append(used_retrievals)

	total_time = end_time - start_time
	total_time -= ratelimit_wait  # Reduce the time spent waiting for rate limits.

	return draft_1, draft_2, all_revisions, evaluator_feedback, draft_3, all_retrievals, total_time


if __name__ == '__main__':
	# Example usage
	user_query = 'What is the capital of France?'
	result = run_pipeline(user_query)
	if result:
		draft_1, draft_2, all_revisions, evaluator_feedback, draft_3, all_retrievals, total_time = result
		log_info(f'Final Draft: {draft_3}')
		log_info(f'Total Retrievals Used: {all_retrievals}')
		log_info(f'Total Time Taken: {total_time:.2f} seconds')
	else:
		log_error('Pipeline execution failed due to unsafe prompt.')
