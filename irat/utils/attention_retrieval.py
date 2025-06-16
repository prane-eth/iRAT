from irat.utils.logger import log_debug, log_info

from sentence_transformers import CrossEncoder


model_name = 'cross-encoder/ms-marco-MiniLM-L6-v2'  # 22.7M params - 3.3M downloads on Huggingface
model_name_short = 'ms-marco-MiniLM-L6-v2'

model = CrossEncoder(model_name)
log_info(f'Loaded CrossEncoder model: ({model_name_short})')


# top_k can be high because many paragraphs are in each page

def select_paragraphs(query: str, paragraphs: list[str], top_k: int, score_threshold: float) -> list[float]:
	results = model.rank(query, paragraphs, top_k, return_documents=True)
	# [{'corpus_id': 2, 'score': 0.94370663, 'text': '....'}, ....]
	selected_paragraphs = []
	for result in results:
		# log_debug(f'Score: {result["score"]}, Text: {result["text"][:50]}...')
		if result['score'] >= score_threshold:
			selected_paragraphs.append(result['text'])
	return selected_paragraphs

if __name__ == '__main__':
	test_query = 'What is the capital of France?'
	test_paragraphs = ['Capital and largest city of France',
		'By the end of the 12th century, Paris had become the political, economic, religious, and cultural capital of France.',
		'With 200,000 inhabitants in 1328, Paris, then already the capital of France, was the most populous city of Europe.',
		'Due to the Parisian uprisings during theFrondeFrondecivil war,Louis XIVLouis XIVmoved his court to a new palace,VersaillesVersailles, in 1682']
	results = select_paragraphs(test_query, test_paragraphs)
	print('Selected Paragraphs:', results)
