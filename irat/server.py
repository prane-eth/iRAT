# API similar to OpenAI API, to allow calls to iRAT and old RAT.
# And a web page to chat with the models using both iRAT and old RAT.

from irat.utils.logger import log_debug
from old_rat import rat as old_rat
from irat.pipeline import run_pipeline


# ------------------------ API server ------------------------

# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
import uvicorn

# from typing import List
from dotenv import load_dotenv
import os

load_dotenv(override=True)
LLM_model = os.getenv('LLM_NAME')

host = '0.0.0.0'

def get_old_rat_response(prompt):
	draft, answer = old_rat(prompt)
	answer = answer[0] if isinstance(answer, list) else answer
	if not answer:
		answer = 'No answer found.'
	answer = answer.strip()
	return draft, answer

def clear_port(port):
	import socket
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		s.bind((host, port))
	except OSError as e:
		if e.errno == 98:  # Address already in use
			log_debug(f'Port {port} is already in use. Clearing it...')
		else:
			raise
	finally:
		s.close()


# class Message(BaseModel):
# 	role: str
# 	content: str

# class ChatRequest(BaseModel):
# 	# model: str  # You can ignore this if not used
# 	messages: List[Message]

# app = FastAPI()

# @app.post('/iRAT/chat/completions')
# def irat_endpoint(request: ChatRequest):
# 	try:
# 		# Get the last user message (simplified for demo)
# 		prompt = request.messages[-1].content
# 		answer = run_pipeline(prompt)
# 		return {
# 			'id': '123',
# 			'object': 'chat.completion',
# 			'created': 0,
# 			'model': LLM_model,
# 			'choices': [
# 				{
# 					'index': 0,
# 					'message': {'role': 'assistant', 'content': answer},
# 					'finish_reason': 'stop'
# 				}
# 			]
# 		}
# 	except Exception as e:
# 		raise HTTPException(status_code=500, detail=str(e))

# @app.post('/old_rat/chat/completions')
# def old_rat_endpoint(request: ChatRequest):
# 	try:
# 		# Get the last user message (simplified for demo)
# 		prompt = request.messages[-1].content
# 		answer = get_old_rat_response(prompt)
# 		return {
# 			'id': '123',
# 			'object': 'chat.completion',
# 			'created': 0,
# 			'model': LLM_model,
# 			'choices': [
# 				{
# 					'index': 0,
# 					'message': {'role': 'assistant', 'content': answer},
# 					'finish_reason': 'stop'
# 				}
# 			]
# 		}
# 	except Exception as e:
# 		raise HTTPException(status_code=500, detail=str(e))

# @app.get('/')
# def root():
# 	return 'Working.'

# def start_api():
# 	port = 8000
# 	log_debug('Starting API server...')
# 	log_debug(f'API URL: http://{host}:{port}/')
# 	# clear the port if it is already in use
# 	clear_port(port)
# 	try:
# 		# assuming this filename is server.py
# 		uvicorn.run('server:app', host=host, port=port, log_level='info')
# 	except KeyboardInterrupt:
# 		log_debug(f'API: KeyboardInterrupt')

# Usage:
'''
import openai
# can be set in .env
openai.base_url = 'http://localhost:8000/iRAT/'

response = openai.chat.completions.create(
	messages=[{'role': 'user', 'content': 'Hi'}],
	model='<any-model-name>',
)
log_debug(response.choices[0].message.content)
'''

# ------------------------ Web page server ------------------------

import gradio as gr

def get_response(project, prompt):
	if project == 'Old RAT':
		return get_old_rat_response(prompt)
	elif project == 'iRAT':
		return run_pipeline(prompt)
	else:
		return 'Invalid project selection.'

from gradio.themes.base import Base as BaseTheme

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
	submit.click(get_response, inputs=[project, prompt], outputs=[output, last_draft])

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
