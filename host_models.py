#!/usr/bin/env python3

# Hosting models through an API
# Why host the models?
# - When we restart the evaluator or the server, we should not wait for the models to load repeatedly.
# - We can host the models on a server and access them through an API.

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime
import pytz
import psutil
import uvicorn
import time
from sentence_transformers import CrossEncoder, SentenceTransformer

import os
from dotenv import load_dotenv
load_dotenv()

if not os.getenv('HF_TOKEN').strip():
	raise ValueError('HF_TOKEN environment variable is not set.')

app = FastAPI()

SERVER_ID = os.getenv('SERVER_ID')


print('Loading models...')

# ------------------ Reasoning Chain Evaluator ------------------

print('Loading Reasoning Chain Evaluator model...')
from transformers import pipeline
reasoning_chain_evaluator = pipeline('text-generation',
					model='uoacollab101/iRAT-ReasoningChainEvaluatorv2',
					device='cpu', trust_remote_code=True)
# CPU is required. Local GPU memory is typically insufficient for this model.

print('Loaded Reasoning Chain Evaluator model.')
class CompletionsRequest(BaseModel):
	model: str
	prompt: Union[str, List[str]]
	max_tokens: Optional[int] = 16
	temperature: Optional[float] = 0.1
	top_p: Optional[float] = 0.9
@app.post('/completions')
def evaluate_reasoning_chain(req: CompletionsRequest):  # OpenAI-compatible endpoint
	# To evaluate reasoning chains using the reasoning chain evaluator model.
	feedback = reasoning_chain_evaluator(
		req.prompt,
		max_new_tokens=req.max_tokens,
		temperature=req.temperature,
		top_p=req.top_p,
		# More values that can't be set via OpenAI API:
		top_k=5,
		no_repeat_ngram_size=2,
		eos_token_id=reasoning_chain_evaluator.tokenizer.eos_token_id,
		clean_up_tokenization_spaces=True,
	)[0]['generated_text']
	return { 'choices': [{ 'text': feedback.strip() }]}


# ------------------ Reranking Model ------------------
print('Loading the ranking model...')
ranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2')

class RerankRequest(BaseModel):
	query: str
	documents: List[str]
	top_n: int
@app.post('/v2/rerank')  # Cohere-compatible endpoint
def score_texts(req: RerankRequest):
	# To get a list of relevant documents based on a query.
	results = ranker.rank(req.query, req.documents,
				req.top_n, return_documents=True)
	new_results = []
	for result in results:
		new_results.append({
			'corpus_id': result['corpus_id'],
			'relevance_score': float(result['score']),
			'document': { 'text': result['text'] },
		})
	return { 'results': new_results }


# ------------------ Embedding Model ------------------

print('Loading the embedding model...')
embed_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

class EmbedRequest(BaseModel):
	# alias the Pydantic field `inputs` to the JSON key 'input'
	inputs: List[str] = Field(..., alias='input')
	class Config:
		validate_by_name = True
@app.post('/embeddings')
def embed_texts(req: EmbedRequest):  # OpenAI-compatible endpoint
	# To embed texts using the sentence-transformer model.
	embeddings = embed_model.encode(req.inputs)
	return {'data': [
		{ 'index': idx, 'object': 'embedding', 'embedding': embedding.tolist() }
		for idx, embedding in enumerate(embeddings)
	]}



ist = pytz.timezone('Asia/Kolkata')
def get_memory_usage():
	used = psutil.virtual_memory().used / (1024 * 1024)  # Convert bytes to MB
	total = psutil.virtual_memory().total / (1024 * 1024)  # Convert bytes to MB
	return f'{used:.2f} MB / {total:.2f} MB ({used / total * 100:.2f}%)'


@app.get('/')
@app.get('/ping')
@app.get('/health')
def root_test():
	current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S %p %Z')
	return {
	 	'message': 'Model hosting service is running at ' + str(current_time),
		'Memory usage': get_memory_usage(),
	}


if __name__ == '__main__':
	while True:
		try:
			# Start the FastAPI server
			print('Starting the FastAPI server...')
			uvicorn.run(app, host='0.0.0.0', port=8000)
			break
		except KeyboardInterrupt:
			print('Server stopped by user.')
			break
		except Exception as e:
			print(f'Error starting the server: {e}.')
			print('Retrying in 5 seconds...')
			time.sleep(5)

