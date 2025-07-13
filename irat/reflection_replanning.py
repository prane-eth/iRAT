# Reflection & replanning

from irat.utils.common_functions import print_separator
from irat.utils.lm_functions import get_response
from irat.utils.logger import log_error, log_info, log_debug
from irat.utils.settings import env
import openai

if not env('HF_TOKEN'):
	raise ValueError('HF_TOKEN environment variable is not set.')
if not env('EVALUATOR_API_URL'):
	raise ValueError('EVALUATOR_API_URL environment variable is not set.')

openai.base_url = env('EVALUATOR_API_URL')

def evaluator_pipeline(prompt, **kwargs):
	# rename 'max_new_tokens' to 'max_tokens' for compatibility with OpenAI API
	if 'max_new_tokens' in kwargs:
		kwargs['max_tokens'] = kwargs.pop('max_new_tokens')
	unsupported_params = ('top_k', 'no_repeat_ngram_size', 'eos_token_id',
							'clean_up_tokenization_spaces')
	for param in unsupported_params:
		if param in kwargs:
			raise ValueError(f'{param} is not supported by OpenAI package. Set the value in the model server.')
	if kwargs.get('do_sample'):
		if 'temperature' not in kwargs and 'top_p' not in kwargs:
			raise ValueError('do_sample requires values to be set.')
		del kwargs['do_sample']  # OpenAI API does not support do_sample
	response = openai.completions.create(
		model='Any',
		prompt=prompt,
		**kwargs
	)
	response_text = response.choices[0].text
	return [{ 'generated_text': response_text }]

try:
	log_info('Testing the evaluator...')
	evaluator_pipeline('hi')  # Test the model encoding function
except Exception as e:
	log_error(f'Error in model: {e}')
	raise RuntimeError('Failed to initialize the evaluator model. Run the server.')
	# run_vllm_command(embed_model_name, task='embed', port=8002)



def get_evaluator_feedback(query, previous_thoughts: str, new_thoughts: str) -> str:
	# Passes the reasoning chain and question to the model and returns concise feedback.
	prompt = (
		'You are a logic and facts expert. Consider various aspects to be factual and give the type of reasoning.\n'
		f'Question: {query}\n-----\n'
		f'Reasoning Chain: {new_thoughts}\n-----\n'
		'Give very very concise Feedback with only one of the following options:\n'
		'1. Correct chain\n'
		'2. Simple error\n'
		'3. Contradiction\n'
		'4. Missing steps\n'
		'5. Irrelevant information'
	)
	# Return raw feedback text from the evaluator model.
	feedback = evaluator_pipeline(
		prompt,
		max_new_tokens=60,
		# More parameters adjusted for concise feedback
		do_sample=True,       # Enable sampling
		top_p=0.9,            # Top-p nucleus sampling
		temperature=0.1,
		# top_k=5,              # Top-k sampling — limits to top 5 tokens
		# no_repeat_ngram_size=2,
		# eos_token_id=evaluator_pipeline.tokenizer.eos_token_id,
		# clean_up_tokenization_spaces=True,
	)[0]['generated_text']
	# feedback = evaluate_chain(prompt)

	# strip echoed prompt(s)
	if feedback.startswith(prompt):
		feedback = feedback[len(prompt):].lstrip()
	return feedback.strip()

