# Server to create web page to chat with the models using both iRAT and old RAT.

from irat.utils.logger import log_debug, log_info
from irat.utils.settings import env
from irat.old_rat import rat as old_rat
from irat.pipeline import run_pipeline
from irat.utils.common_functions import host, clear_port, print_separator
import gradio as gr
from gradio.themes.base import Base as BaseTheme


def get_old_rat_response(prompt):
	draft, answer = old_rat(prompt)
	answer = answer[0] if isinstance(answer, list) else answer
	if not answer:
		answer = 'No answer found.'
	answer = answer.strip()
	return draft, answer


def get_response(project, prompt):
	if project == 'Old RAT':
		initial_draft, answer = get_old_rat_response(prompt)
		return initial_draft, answer
	elif project == 'iRAT':
		response_result = run_pipeline(prompt)
		if response_result is None:
			print_separator()
			return 'Not available', 'Error: Query seems to be against our policies.'
		draft_1, draft_2, all_revisions, evaluator_feedback, final_answer, \
			all_retrievals, total_time = response_result
		return evaluator_feedback, final_answer
	else:
		return 'Invalid project selection.', 'Invalid project selection.'


# Create a custom theme with larger font sizes
class LargeFontTheme(BaseTheme):
	def __init__(self):
		super().__init__() # text_size='lg' or sm, md, lg, xl, xxl
		self.set(
			# body_text_size='18px',
			# input_text_size='18px',
			# section_header_text_size='22px',
			block_info_text_size='18px',
			block_label_text_size='20px',
			block_title_text_size='24px',
		)

# Gradio interface
with gr.Blocks(theme=LargeFontTheme()) as demo:
	# gr.Markdown('## Select Project and Enter Prompt')
	project = gr.Radio(['iRAT', 'Old RAT'], label='Choose a project')
	prompt = gr.Textbox(label='Enter your prompt')
	gr.Markdown('---')  # separator
	output = gr.Textbox(label='Get the model output')  # or gr.Markdown
	last_draft = gr.Textbox(label='Last thoughts')
	submit = gr.Button('Submit')
	submit.click(get_response, inputs=[project, prompt], outputs=[last_draft, output])

def start_gradio():
	port = 1776
	clear_port(port)
	log_debug(f'Web page URL: http://{host}:{port}/?__theme=light')
	try:
		demo.launch(server_name=host, server_port=port, show_api=False)  # prevent_thread_lock=True
	except KeyboardInterrupt:
		log_debug('Web page: KeyboardInterrupt')

start_gradio()

# from threading import Thread

# if __name__ == '__main__':
# 	fastapi_thread = Thread(target=start_api)
# 	fastapi_thread.start()
# 	gradio_thread = Thread(target=start_gradio)
# 	gradio_thread.start()

# 	try:
# 		fastapi_thread.join()
# 		gradio_thread.join()
# 	except KeyboardInterrupt:
# 		fastapi_thread.join(timeout=-1)
# 		gradio_thread.join(timeout=-1)
# 		log_debug('Server stopped by user.')
