from irat.utils.logger import log_debug
import cohere

co = cohere.ClientV2()

def select_paragraphs(query: str, paragraphs: list[str], top_k: int, score_threshold: float) -> list[float]:
	rerank_result = co.rerank(
		model='Any',
		query=query,
		documents=paragraphs,
		top_n=top_k,
	)
	selected_paragraphs = []
	for result in rerank_result.results:
		if result.relevance_score >= score_threshold:
			selected_paragraphs.append(paragraphs[result.corpus_id])
	return selected_paragraphs

# Test the model and raise error if it fails to load
try:
	select_paragraphs('Test query', ['Test paragraph 1', 'Test paragraph 2'], top_k=1, score_threshold=0.5)
except Exception as e:
	raise RuntimeError(f'Failed to initialize the ranking model. Please start the server.')



if __name__ == '__main__':
	# Example usage
	test_query = 'What is the capital of France?'
	test_paragraphs = ['Capital and largest city of France',
		'By the end of the 12th century, Paris had become the political, economic, religious, and cultural capital of France.',
		'With 200,000 inhabitants in 1328, Paris, then already the capital of France, was the most populous city of Europe.',
		'Due to the Parisian uprisings during theFrondeFrondecivil war,Louis XIVLouis XIVmoved his court to a new palace,VersaillesVersailles, in 1682']
	selected_paragraphs = select_paragraphs(test_query, test_paragraphs, top_k=3, score_threshold=5.0)
	log_debug('Selected Paragraphs:', selected_paragraphs)
