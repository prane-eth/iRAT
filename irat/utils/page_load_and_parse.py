from irat.utils.logger import log_debug, log_error, log_info

import asyncio
from bs4 import BeautifulSoup
from langchain_community.document_loaders import AsyncHtmlLoader, AsyncChromiumLoader
from readability import Document as ReadabilityDocument
import requests


def load_api_url(url: str) -> str:
	response = requests.get(url)
	if response.status_code != 200:
		log_debug(f'Error fetching API URL: {response.status_code} - {response.text}')
		if 'too many requests' in response.text or 'Unable to connect' in response.text:
			with open('error.txt', 'w') as file:
				file.write(response.text)
		response.raise_for_status()
	data = response.json()
	if 'items' not in data or not data['items']:
		log_debug(f'No items found')
		log_debug(f'API URL', url)
		return None
	return data

def scrape_stackoverflow(url: str, site: str = 'stackoverflow') -> tuple[str, list[str]]:
	log_debug('Using Stackoverflow API')
	if 'questions/' in url:
		question_id = url.split('questions/')[1].split('/')[0]
	if not question_id or not question_id.isdigit():
		log_debug(f'Invalid StackOverflow question ID in URL: {url}')
		return None

	# Adding the question details adds context and shows relevance to the answers during attention-retrieval stage.
	question_api_url = f'https://api.stackexchange.com/2.3/questions/{question_id}?site={site}&filter=withbody'
	data = load_api_url(question_api_url)
	question = data['items'][0]['title'].strip() + ' ' + data['items'][0]['body'].strip()

	answer_api_url = f'https://api.stackexchange.com/2.3/questions/{question_id}/answers?order=desc&sort=votes&site={site}&filter=withbody'
	data = load_api_url(answer_api_url)
	answers = [item['body'].strip() for item in data['items']]
	if not answers:
		log_debug(f'No valid answers found for question ID {question_id}')
		return None
	answers = answers[:10]  # Limit to first 10 answers
	return '\n\n'.join([question] + answers)  # , answers


class ParagraphExtractor:
	def __init__(self):
		self.paragraph_tags = ['p', 'code', 'blockquote']
		self.heading_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
		self.list_tags = ['li', 'ul', 'ol']
		self.all_tags = self.paragraph_tags + self.heading_tags + self.list_tags

	def extract_main_paragraphs_from_html(self, doc) -> list[str]:
		reader = ReadabilityDocument(doc.page_content.strip())
		cleaned_html = reader.summary(html_partial=True)

		soup = BeautifulSoup(cleaned_html, 'html5lib')
		paragraphs: list[str] = []
		for part in soup.find_all(self.all_tags):
			text = part.get_text().strip()
			if not text:
				continue

			## temporarily avoid special characters to save tokens
			if part.name in self.heading_tags:
				level = int(part.name[1])  # heading level like '1' from h1
				text = f'{"#" * level} {text}'  # Markdown heading
			elif part.name in self.list_tags:
				if part.name == 'ol':
					text = f'1. {text}'
				else:
					text = f'- {text}'
			elif part.name == 'blockquote':
				text = f'> {text}'
			elif part.name == 'p':
				# Process <p> tag to handle bold/italic formatting
				text = ''
				for child in part.descendants:
					child_text = child.get_text().strip()
					if child.name in ['b', 'strong']:  # bold text
						text += f'**{child_text}**'
					elif child.name in ['i', 'em']:  # italic text
						text += f'_{child_text}_'
					else:
						text += child_text
				text = text.strip()
			elif part.name == 'code':
				text = f'`{text}`'

			if part.name in self.paragraph_tags:
				paragraphs.append(text)
		content = '\n\n'.join(paragraphs)
		doc.page_content = content
		return doc, paragraphs

	def transform_documents(self, docs: list) -> tuple[list['Doc'], list[list[str]]]:
		transformed_docs = []
		page_paragraphs: list[str] = []
		for doc in docs:
			try:
				transformed_doc, paragraphs = self.extract_main_paragraphs_from_html(doc)
				transformed_docs.append(transformed_doc)
				page_paragraphs.extend(paragraphs)
			except Exception as e:
				if 'Document is empty' in str(e):
					log_info('Document empty')
				else:
					log_error(f'Error processing document: {e}')
				continue
		return transformed_docs, page_paragraphs


text_transformer = ParagraphExtractor()


async def get_one_page_content_async(url: str, use_chromium: bool = False, only_html: bool = False):
	if not url:
		log_error('No URL provided')
		return None
	if 'stackoverflow.com' in url:
		return scrape_stackoverflow(url, site='stackoverflow')
	elif 'stackexchange.com' in url:
		# get the word before .stackexchange.com
		site = url.split('.stackexchange.com')[0].split('//')[-1]
		return scrape_stackoverflow(url, site=site)
	elif 'superuser.com' in url:
		return scrape_stackoverflow(url, site='superuser')
	elif 'mathoverflow.net' in url:
		return scrape_stackoverflow(url, site='mathoverflow')
	elif 'serverfault.com' in url:
		return scrape_stackoverflow(url, site='serverfault')
	elif 'askubuntu.com' in url:
		return scrape_stackoverflow(url, site='askubuntu')
	

	if use_chromium:
		log_info('Using Chromium loader for JavaScript rendering')
		try:
			loader = AsyncChromiumLoader([url])  # handles JavaScript rendering
		except Exception as e:
			log_error(f'Error initializing AsyncChromiumLoader: {e}')
			return None
	else:
		loader = AsyncHtmlLoader([url])

	docs = await loader.aload()
	if not docs:
		return None

	docs_transformed, page_paragraphs = text_transformer.transform_documents(docs)
	if not docs_transformed:
		return None
	page_content = docs_transformed[0].page_content.strip()
	if not page_content:
		return None

	# if parsing failed and JavaScript is required
	if page_content.startswith('Enable JavaScript'):
		return None
	if 'Verifying you are human' in page_content:
		log_error('Loading failed due to bot protection:', url)
		return None

	return page_content


# Fetch one page at a time
def get_page_contents(urls: list, use_chromium: bool = False, only_html: bool = False):
	if not urls or not isinstance(urls, list):
		log_error('Please provide a list of URLs.')
		return []

	contents = []
	# Each page content is a list of paragraphs. Combine all the lists.
	for url in urls:
		try:
			content = asyncio.run(get_one_page_content_async(url, use_chromium, only_html))
			if content is None:
				log_error(f'Failed to load content from {url}')
				continue
			contents.append(content)
		except Exception as e:
			log_error(f'Error processing URL {url}: {e}')

	return contents



if __name__ == '__main__':
	# Example usage
	test_urls = [
		'https://www.w3schools.com/html/html_editors.asp',
		'https://www.geeksforgeeks.org/python/python-data-structures/',
		'https://stackoverflow.com/questions/12345620/',
		'https://docs.python.org/3/tutorial/datastructures.html',
		'https://www.coursera.org/learn/python-data',
		'https://www.datacamp.com/tutorial/data-structures-python',
	]
	import time
	print('Loading pages...')
	start_time = time.time()
	contents = get_page_contents(test_urls)
	end_time = time.time()
	print(f'\n Fetched {len(contents)} pages in {end_time - start_time:.2f} seconds \n')
	for content in contents:
		print(content[:500])  # Print first 500 characters of each content
		break
