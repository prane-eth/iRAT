# Wraps OpenAI/Transformers calls for “initial draft”
from irat.utils.common_functions import get_date, user_message, system_message
from irat.utils.logger import log_info
from irat.utils.settings import env
from openai import OpenAI

default_model = env('LLM_NAME')
client = OpenAI()

knowledge_cutoff = env('LLM_KNOWLEDGE_CUTOFF')

def get_cutoff_text() -> str:
	return f'Your knowledge cutoff: {knowledge_cutoff}. Current date: {get_date()}. \n'

def get_response(prompt: str, model: str = default_model) -> str:
	# Get a response through OpenAI package.
	response = client.chat.completions.create(
		model=model,
		messages=[
			system_message(get_cutoff_text()),
      		user_message(prompt),
        ],
	)
	return response.choices[0].message.content.strip()

def split_draft(draft: str, split_char: str = '\n\n') -> list[str]:
	# Split the draft into multiple paragraphs
	draft_paragraphs = draft.split(split_char)
	# log_info(f'The draft answer has {len(draft_paragraphs)}')
	return draft_paragraphs


import tiktoken

def count_tokens(string: str, encoding_name: str = 'cl100k_base') -> int:
	'''Returns the number of tokens in a text string.'''
	encoding = tiktoken.get_encoding(encoding_name)
	num_tokens = len(encoding.encode(string))
	return num_tokens

def chunk_text_by_sentence(text: str, chunk_size: int = 2048) -> list[str]:
	'''Chunk the $text into sentences with less than 2k tokens.'''
	sentences = text.split('. ')
	chunked_text = []
	curr_chunk = []
	# Add text snippets sentence by sentence, making sure each paragraph is less than 2k tokens
	for sentence in sentences:
		if count_tokens('. '.join(curr_chunk)) + count_tokens(sentence) + 2 <= chunk_size:
			curr_chunk.append(sentence)
		else:
			chunked_text.append('. '.join(curr_chunk))
			curr_chunk = [sentence]
	# Add the last snippet
	if curr_chunk:
		chunked_text.append('. '.join(curr_chunk))
	return chunked_text[0]

def chunk_text_front(text: str, chunk_size: int = 2048) -> str:
	'''
	get the first `trunk_size` token of text
	'''
	tokens = count_tokens(text)
	if tokens < chunk_size:
		return text
	else:
		ratio = float(chunk_size) / tokens
		char_num = int(len(text) * ratio)
		return text[:char_num]

def chunk_texts(text: str, chunk_size: int = 2048) -> list[str]:
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
