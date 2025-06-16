# Draft revision using retrieved text

from irat.stage_base import StageBase
from irat.lm_adapter import LMAdapter
from irat.utils.logger import log_debug

lm_adapter = LMAdapter()

class DraftRevision(StageBase):
	STAGE = 'draft_revision'
	# def __init__(self, lm_adapter: LMAdapter = LMAdapter()):
	#     self.lm_adapter = lm_adapter

	def revise(self, draft: str, retrieved_passages: list[str], user_query: str) -> str:
		prompt = (
			'\n'.join(retrieved_passages) + '\n\n'
			' --- \n'
			f'Draft: {draft} \n'
			' --- \n'
			'Revise the draft based on the additional information and user query: \n'
			f'User Query: {user_query} \n'
			' --- \n'
			'Do not mention that I provided you with additional information. \n'
		)
		# log_debug('Draft Revision Prompt:', prompt, '\n\n')
		return lm_adapter.generate_revision(prompt)


if __name__ == '__main__':
	# Example usage
	draft_revision = DraftRevision()
	draft = 'As an AI language model, I do not have access to real-time information'
	retrieved_passages = [
		'OpenAI is an AI research and deployment company.',
		'OpenAI has developed several AI models, including GPT-3.',
		'GPT-3 is known for its ability to generate human-like text.',
	]
	user_query = 'What is OpenAI?'
	revised_response = draft_revision.revise(draft, retrieved_passages, user_query)
	print('Revised Response:', revised_response.strip())