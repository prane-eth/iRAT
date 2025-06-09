# API similar to OpenAI API, to allow calls to iRAT and old RAT.

from old_rat import LLM_model, rat as old_rat

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from typing import List


class Message(BaseModel):
	role: str
	content: str

class ChatRequest(BaseModel):
	# model: str  # You can ignore this if not used
	messages: List[Message]

app = FastAPI()

from irat.pipeline import Pipeline
irat_pipeline = Pipeline()

@app.post('/iRAT/chat/completions')
def irat_endpoint(request: ChatRequest):
	try:
		# Get the last user message (simplified for demo)
		prompt = request.messages[-1].content
		answer = irat_pipeline.run(prompt)
		return {
			'id': '123',
			'object': 'chat.completion',
			'created': 0,
			'model': LLM_model,
			'choices': [
				{
					'index': 0,
					'message': {'role': 'assistant', 'content': answer},
					'finish_reason': 'stop'
				}
			]
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

@app.post('/old_rat/chat/completions')
def old_rat_endpoint(request: ChatRequest):
	try:
		# Get the last user message (simplified for demo)
		prompt = request.messages[-1].content
		draft, answer = old_rat(prompt)
		return {
			'id': '123',
			'object': 'chat.completion',
			'created': 0,
			'model': LLM_model,
			'choices': [
				{
					'index': 0,
					'message': {'role': 'assistant', 'content': answer},
					'finish_reason': 'stop'
				}
			]
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
	print('Starting FastAPI server...')
	# assuming this filename is server.py
	uvicorn.run('server:app', host='0.0.0.0', port=8000, log_level='info')

# Usage:
'''
import openai
# can be set in .env
openai.base_url = 'http://localhost:8000/iRAT/'

response = openai.chat.completions.create(
    messages=[{'role': 'user', 'content': 'Hi'}],
    model='<any-model-name>',
)
print(response.choices[0].message.content)
'''