# Wraps OpenAI/Transformers calls for “initial draft”
from irat.utils.common_functions import get_current_month, user_message, system_message
from irat.utils.logger import log_debug, log_error, log_info
from irat.utils.ratelimit_counter import wait_for_rate_limit
from irat.utils.settings import env
import openai
import tiktoken

model = env('LLM_NAME')

if env('AZURE_OPENAI_ENDPOINT'):
	client = openai.AzureOpenAI()
else:
	client = openai.OpenAI()

knowledge_cutoff = env('LLM_KNOWLEDGE_CUTOFF')
cutoff_text = f'Your knowledge cutoff: {knowledge_cutoff}. Current date: {get_current_month()}. \n'


def get_response(prompt: str, use_sys_message=False) -> str:
	# Get a response through OpenAI package.
	attempt_limit = 3
	for attempt in range(attempt_limit):
		try:
			messages = [
				user_message(prompt),
			]
			if use_sys_message:
				messages.insert(0, system_message(cutoff_text))
			response = client.chat.completions.create(
				model=model,
				messages=messages,
			)
			response = response.choices[0].message.content.strip()
			# wait_for_rate_limit(5)  # To avoid rate limits
			return response
		except openai.RateLimitError:
			if attempt == attempt_limit - 1:
				log_error(f'Rate limit reached after {attempt + 1} attempts.' \
							'Failed to get a response.')
				return None
			log_info(f'Rate limit reached. Waiting...')
			wait_for_rate_limit(30)  # Wait before retrying
			if attempt == 1:  # 2nd attempt. Wait more.
				wait_for_rate_limit(20)
		except openai.BadRequestError as e:
			log_error(f'Bad request error: {e}. Prompt: {prompt}')
			return None
		except Exception as e:
			log_error(f'Error in OpenAI API call: {e}.')
			wait_for_rate_limit(5)
		log_debug(f'Retrying {attempt + 1}/3...')
		if attempt == 2:
			log_error('Failed to get a response after 3 attempts.')
			return None


def split_draft(draft: str, split_char: str = '\n\n') -> list[str]:
	# Split the draft into multiple paragraphs
	draft_paragraphs = draft.split(split_char)
	draft_paragraphs = [p.strip() for p in draft_paragraphs if p.strip()]  # Remove empty paragraphs

	# To prevent rate limits or other delays, merge consecutive paragraphs if they are short.
	new_draft_paragraphs = draft_paragraphs[:1]
	for paragraph in draft_paragraphs[1:]:
		if len(new_draft_paragraphs[-1]) + len(paragraph) < 500:
			new_draft_paragraphs[-1] += ' ' + paragraph
		else:
			new_draft_paragraphs.append(paragraph)
	draft_paragraphs = new_draft_paragraphs

	# log_info(f'The draft answer has {len(draft_paragraphs)}')
	return draft_paragraphs


def count_tokens(string: str, encoding_name: str = 'cl100k_base') -> int:
	'''Returns the number of tokens in a text string.'''
	encoding = tiktoken.get_encoding(encoding_name)
	num_tokens = len(encoding.encode(string))
	return num_tokens


def chunk_texts(text: str, chunk_size: int) -> list[str]:
	'''
	trunk the text into n parts, return a list of text
	[text, text, text]
	'''
	tokens = count_tokens(text)
	if tokens < chunk_size:
		return [text]
	else:
		n = int(tokens/chunk_size) + 1
		# Calculate the length of each section
		part_length = len(text) // n
		# If it is not divisible, the last part will contain extra characters.
		extra = len(text) % n
		parts = []
		start = 0

		for i in range(n):
			# For the first extra parts, one more character is allocated to each part
			end = start + part_length + (1 if i < extra else 0)
			parts.append(text[start:end])
			start = end
		return parts
