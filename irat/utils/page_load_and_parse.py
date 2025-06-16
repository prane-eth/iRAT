from bs4 import BeautifulSoup
from langchain_community.document_loaders import AsyncHtmlLoader, AsyncChromiumLoader
from readability import Document as ReadabilityDocument

import asyncio


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
					if child.name in ['b', 'strong']:  # bold text
						text += f'**{child.get_text().strip()}**'
					elif child.name in ['i', 'em']:  # italic text
						text += f'_{child.get_text().strip()}_'
					elif child.string:  # child element with text
						text += child.string.strip()
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
				print(f'Error processing document: {e}')
				continue
		return transformed_docs, page_paragraphs


text_transformer = ParagraphExtractor()

async def get_one_page_content_async(url: str, use_chromium: bool = False, only_html: bool = False):
	if not url:
		print('No URL provided')
		return None
	if use_chromium:
		print('Using Chromium loader for JavaScript rendering')
		try:
			loader = AsyncChromiumLoader([url])  # handles JavaScript rendering
		except Exception as e:
			print(f'Error initializing AsyncChromiumLoader: {e}')
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
		if use_chromium:  # If JS failed even with Chromium
			raise ValueError('JavaScript rendering failed')
		# try using Chromium loader
		page_content = await get_one_page_content_async(url, use_chromium=True)
		if not page_content:
			return None
	if 'Verifying you are human' in page_content:
		print('Loading failed due to bot protection:', url)
		return None

	return page_content, page_paragraphs


def get_page_contents(urls: list, use_chromium: bool = False, only_html: bool = False):
	if not urls or not isinstance(urls, list):
		print('Please provide a list of URLs.')
		return []

	contents = []
	paragraphs_list: list[list[str]] = []
	# Each page content is a list of paragraphs. Combine all the lists.
	for url in urls:
		try:
			content, page_paragraphs = asyncio.run(get_one_page_content_async(url, use_chromium, only_html))
			if content is None:
				print(f'Failed to load content from {url}')
				continue
			contents.append(content)
			paragraphs_list.append(page_paragraphs)
		except Exception as e:
			print(f'Error processing URL {url}: {e}')

	return contents, paragraphs_list

