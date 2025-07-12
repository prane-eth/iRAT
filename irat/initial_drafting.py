from irat.utils.lm_functions import get_response
from irat.utils.logger import log_info


DRAFT_PROMPT = '''
IMPORTANT:
Try to answer this question/instruction with step-by-step thoughts and make the answer more structural.
Use `\n\n` to split the answer into several paragraphs.
Just respond to the instruction directly. DO NOT add additional explanations or introducement in the answer unless you are asked to.
'''

def generate_initial_draft(user_query: str) -> str:
	log_info('Fetching the draft...')
	draft = get_response(user_query + DRAFT_PROMPT, use_sys_message=True)
	return draft.strip()
