# Result filtering module to filter search results using spam filtering and Attention-Retrieval

from irat.utils.attention_retrieval import select_paragraphs
from irat.utils.domain_filter import filter_urls
from irat.utils.lm_functions import chunk_texts
from irat.utils.logger import log_debug, log_error, log_info
from irat.utils.page_load_and_parse import get_page_contents

def fetch_and_filter_results(question: str, urls: list[str], limit: int = 1) -> list[str]:
	if not urls:
		log_info('No URLs provided for filtering.')
		return []

	filtered_urls = filter_urls(urls)  # remove suspicious URLs
	# log_debug('Filtered URLs:', filtered_urls)
	if not filtered_urls:
		log_info('No valid URLs found after filtering.')
		return []
	filtered_urls = filtered_urls[:limit]  # limit the number of URLs to process
	unused_urls = urls[len(filtered_urls):]  # These can be used if no results are found.
	log_debug('Using URLs:', filtered_urls)

	contents = get_page_contents(filtered_urls)  # get contents of the pages
	# log_debug('Page Contents:', contents)
	if not contents:
		log_info('No valid page contents found for filtering.')
		if unused_urls:
			return fetch_and_filter_results(question, unused_urls, limit)
		else:
			return None

	# Divide each page into chunks
	chunks = []
	for page_content in contents:
		if not page_content:
			log_info('Empty page content found. Skipping.')
			continue
		if len(page_content) > 10_000:
			log_info(f'Page is too long ({len(page_content)} characters). Considering less characters')
			page_content = page_content[:10_000]
		chunks += chunk_texts(page_content, chunk_size=370)

	# apply attention-retrieval method
	selected_paragraphs = select_paragraphs(question, chunks, top_k=8, score_threshold=5.0)
 	# 	- top_k can be high because many paragraphs are in each page.
	# 	- score_threshold is low because chunks are small and get lesser scores.
	# log_debug('Selected Paragraphs:', selected_paragraphs)
	if not selected_paragraphs:
		log_info('No paragraphs selected after filtering.')
		if unused_urls:
			return fetch_and_filter_results(question, unused_urls, limit)
		else:
			return None

	# To prevent rate limits or other delays, merge consecutive paragraphs if they are short.
	new_selected_paragraphs = selected_paragraphs[:1]
	for paragraph in selected_paragraphs[1:]:
		if len(new_selected_paragraphs[-1]) + len(paragraph) < 500:
			new_selected_paragraphs[-1] += ' ' + paragraph
		else:
			new_selected_paragraphs.append(paragraph)
	selected_paragraphs = new_selected_paragraphs

	return selected_paragraphs


if __name__ == '__main__':
	# Example usage
	question = 'What is the first repeated character in a given string?'
	urls = ['https://stackoverflow.com/questions/50976511/code-to-output-the-first-repeated-character-in-given-string']
	try:
		results = fetch_and_filter_results(question, urls, 1)
		log_debug('Filtered Results:', len(results))
		for result in results[:1]:  # Display the first result
			log_debug(result)
	except Exception as e:
		log_error('Error:', e)
