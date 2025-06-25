#!/usr/bin/env python3

# Hosting models through an API

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime
import pytz
import psutil
import uvicorn
import time

import os
from dotenv import load_dotenv
status = load_dotenv()
if not status:
	raise ValueError('Failed to load environment variables from .env file.')
if not os.getenv('HF_TOKEN'):
	raise ValueError('HF_TOKEN environment variable is not set.')

app = FastAPI()

SERVER_ID = os.getenv('SERVER_ID')

if SERVER_ID == '1':
	print('Loading models...')
	from sentence_transformers import CrossEncoder, SentenceTransformer

	# ------------------ Reranking Model ------------------
	print('Loading the ranking model...')
	ranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2', local_files_only=True)
						# 'cross-encoder/ms-marco-MiniLM-L6-v2'
						# './msmarco-coding-MiniLM-L6-v2'
	print('Loaded the ranking model')
 
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
	embed_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', local_files_only=True)
	print('Loaded the embedding model')
 
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

	# # ------------------ Sentiment Analysis Model ------------------

	# print('Hosting Sentiment Analysis model...')
	# class ClassifyRequest(BaseModel):
	# 	inputs: List[str]

	# from transformers import pipeline
	# sentiment_pipeline = pipeline('sentiment-analysis',
	# 	model='distilbert/distilbert-base-uncased-finetuned-sst-2-english')
	# print('Loaded Sentiment Analysis model.')

	# @app.post('/v1/classify')  # Cohere-compatible endpoint
	# def classify_text(req: ClassifyRequest):
	# 	# To classify text using the cohere model.
	# 	response = sentiment_pipeline(req.inputs)
	# 	return { 'classifications': response }
	# # Example usage:
	# # import cohere
	# # co = cohere.Client(base_url=env('SENTIMENT_API_URL'))
	# # inputs = ['I love this product!', 'This is terrible.']
	# # response = co.classify(
	# # 	inputs=inputs,
	# # 	# output_type='classifications',
	# # ).classifications[0]
	# # return response.label, response.score

else:
	# ------------------ Reasoning Chain Evaluator ------------------
	print('Hosting Reasoning Chain Evaluator model...')
	from transformers import pipeline
	reasoning_chain_evaluator = pipeline('text-generation',
						model='uoacollab101/iRAT-ReasoningChainEvaluatorv2',
						device='cpu', trust_remote_code=True)
	# CPU is required. Local GPU memory is mostly insufficient for this model.
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




# Old code

'''  # Old code to load the model and generate the ranking
from sentence_transformers import CrossEncoder
model = CrossEncoder(model_name)
log_info(f'Loaded CrossEncoder model: ({model_name_short})')
def select_paragraphs(query: str, paragraphs: list[str], top_k: int, score_threshold: float) -> list[float]:
	results = model.rank(query, paragraphs, top_k, return_documents=True)
	# [{'corpus_id': 2, 'score': 0.94370663, 'text': '....'}, ....]
	selected_paragraphs = []
	for result in results:
		# log_debug(f'Score: {result["score"]}, Text: {result["text"][:50]}...')
		if result['score'] >= score_threshold:
			selected_paragraphs.append(result['text'])
	return selected_paragraphs, results
'''

# # Unused vLLM commands to serve the models:
# vllm serve 'cross-encoder/ms-marco-MiniLM-L6-v2' --task score --host 0.0.0.0 --port 8000
# vllm serve 'sentence-transformers/all-MiniLM-L6-v2' --task embed --host 0.0.0.0 --port 8002
# vllm serve uoacollab101/iRAT-ReasoningChainEvaluatorv2 --trust-remote-code --device cpu \
# 	--host 0.0.0.0 --port 8003