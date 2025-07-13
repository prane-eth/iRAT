# A web page to chat with the models using both iRAT and old RAT.

from irat.utils.common_functions import host, clear_port, print_separator
from irat.utils.logger import log_debug, log_error
from irat.utils.prompt_security import UnsafePromptError

from irat.old_rat import rat as old_rat
from irat.pipeline import run_pipeline

import gradio as gr
from gradio.themes.base import Base as BaseTheme



def get_response(project, prompt):
	if project == 'Old RAT':
		initial_draft, answer = old_rat(prompt)
		answer = answer.strip()
		if not answer:
			answer = 'No answer found.'
		return initial_draft, answer

	elif project == 'iRAT':
		try:
			_, draft_2, _, final_answer = run_pipeline(prompt)
			return draft_2, final_answer
		except UnsafePromptError:
			log_error(e)
			print_separator()
			return 'Not available', 'Error: Query seems to be against our policies.'

	return 'Invalid project selection.', 'Invalid project selection.'


# Create a custom theme with larger font sizes
class LargeFontTheme(BaseTheme):
	def __init__(self):
		super().__init__() # text_size='lg' or sm, md, lg, xl, xxl
		self.set(
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

	response = gr.Textbox(label='Get the response')  # or gr.Markdown
	last_draft = gr.Textbox(label='Last thoughts')

	submit = gr.Button('Submit')
	submit.click(get_response, inputs=[project, prompt], outputs=[last_draft, response])


if __name__ == '__main__':
	port = 7000
	clear_port(port)
	log_debug(f'Web page URL: http://{host}:{port}/?__theme=light')
	try:
		demo.launch(server_name=host, server_port=port, show_api=False)  # prevent_thread_lock=True
	except KeyboardInterrupt:
		log_debug('Web page: KeyboardInterrupt')
