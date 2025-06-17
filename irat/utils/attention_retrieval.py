from irat.utils.logger import log_debug, log_info
import cohere

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

model_name = 'cross-encoder/ms-marco-MiniLM-L6-v2'  # 22.7M params - 3.3M downloads on Huggingface
model_name_short = 'ms-marco-MiniLM-L6-v2'

# model_name = 'cross-encoder/ms-marco-MiniLM-L4-v2'  # 22.7M params - 3.3M downloads on Huggingface
# model_name_short = 'ms-marco-MiniLM-L4-v2'


co = cohere.ClientV2()
def select_paragraphs(query: str, paragraphs: list[str], top_k: int, score_threshold: float) -> list[float]:
	rerank_result = co.rerank(
		model=model_name,
		query=query,
		documents=paragraphs,
		top_n=top_k,
	)
	selected_paragraphs = []
	for result in rerank_result.results:
		if result.relevance_score >= score_threshold:
			selected_paragraphs.append(result.document.text)
	return selected_paragraphs

# Test the model and raise error if it fails to load
try:
	select_paragraphs('Test query', ['Test paragraph 1', 'Test paragraph 2'], top_k=1, score_threshold=0.5)
except Exception as e:
	log_info(f'Error loading the model {model_name_short}: {e}')
	raise RuntimeError(f'Failed to load the model {model_name_short}. Please run the vLLM command.')



if __name__ == '__main__':
	test_query = 'What is the capital of France?'
	test_paragraphs = ['Capital and largest city of France',
		'By the end of the 12th century, Paris had become the political, economic, religious, and cultural capital of France.',
		'With 200,000 inhabitants in 1328, Paris, then already the capital of France, was the most populous city of Europe.',
		'Due to the Parisian uprisings during theFrondeFrondecivil war,Louis XIVLouis XIVmoved his court to a new palace,VersaillesVersailles, in 1682']
	selected_paragraphs = select_paragraphs(test_query, test_paragraphs, top_k=3, score_threshold=5.0)
	log_debug('Selected Paragraphs:', selected_paragraphs)
