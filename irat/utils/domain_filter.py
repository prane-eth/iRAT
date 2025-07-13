from irat.utils.logger import log_debug, log_error, log_info
from irat.utils.settings import env

### Pre-process the URLs
from urllib.parse import urlparse

def _is_ip_address(url):
	# Check if the URL is an IP address or has a domain name.
	# IP addresses are not standard sources of information, and shall be removed.
	try:
		parsed_url = urlparse(url)
		ip = parsed_url.hostname
		if ip and all(part.isdigit() for part in ip.split('.')) and len(ip.split('.')) == 4:
			return True
	except ValueError:
		return False
	return False

def preprocess_urls(urls=[]):
	# Remove URLs with protocols other than http and https
	http_urls = [url for url in urls if url.startswith(('http://', 'https://'))]
	# Convert http to https
	# If some sites don't support https, loading fails and the next result will be used automatically.
	http_urls = [url.replace('http://', 'https://') for url in http_urls]
	
	# if the page uses an IP address instead of a domain name, remove it
	http_urls = [url for url in http_urls if not _is_ip_address(url)]

	removed_count = len(urls) - len(http_urls)

	return http_urls, removed_count


### Using Google Safe Browsing API

from pysafebrowsing import SafeBrowsing

__api_keys = env('GOOGLE_SAFEBROWSING_API_KEYS')
__api_keys = [key.strip() for key in __api_keys.split(",") if key.strip() and '#' not in key]
if not __api_keys:
	raise ValueError('Google API key is not set in the settings.')
__key_index = 0
safebrowsing = SafeBrowsing(__api_keys[__key_index])

def change_api_key(error=True):
	global __api_keys
	global __key_index
	log_info('Google Safe Browsing: Switching to the next API key.')
	if error:
		log_info(f'Rate limit exceeded. Removing key: ....{__api_keys[__key_index][-3:]}')
		# Remove the current API key from the list
		__api_keys.pop(__key_index)
		if not __api_keys:
			log_error("Domain filter: No more API keys available. Exiting.")
			with open('error.txt', 'w') as file:
				file.write('Domain filter: No more API keys available. Exiting.')
			raise Exception('Domain filter: No more API keys available. Exiting.')
	else:
		__key_index += 1
	if __key_index >= len(__api_keys):
		__key_index = 0

	global safebrowsing
	safebrowsing = SafeBrowsing(__api_keys[__key_index])


def check_google_safe_browsing(urls=[]):
	try:
		# Check Google Safe Browsing for malicious URLs
		# Returns True if malicious, False otherwise.
		if not urls:
			raise ValueError('No URLs provided for checking.')
		response = safebrowsing.lookup_urls(urls)
		malicious_count = 0
		result = {}
		for url, info in response.items():
			result[url] = True if info['malicious'] else False
			if info['malicious']:
				malicious_count += 1
		return result, malicious_count
	except Exception as e:
		if '429' in str(e):
			change_api_key()
			return check_google_safe_browsing(urls)
		else:
			log_error(f'Google Safe Browsing Error: {e}')
			raise e

# test the function
try:
	check_google_safe_browsing(['https://www.google.com', 'https://www.example.com'])
except Exception as e:
	log_error(f'Error checking Google Safe Browsing: {e}')
	raise e


### Use Kaggle dataset

import requests
import os

# Download and extract the Kaggle dataset if it does not exist
dataset_filename = 'malicious_phish.csv'
if not os.path.exists(dataset_filename):
	# write in python
	url = 'https://www.kaggle.com/api/v1/datasets/download/sid321axn/malicious-urls-dataset'
	zip_filename = url.split('/')[-1] + '.zip'
	if not os.path.exists(zip_filename):
		log_debug(f'Downloading {zip_filename}...')
		response = requests.get(url, allow_redirects=True)
		with open(zip_filename, 'wb') as file:
			file.write(response.content)

	import zipfile
	with zipfile.ZipFile(zip_filename) as zip_file:
		zip_file.extractall('.')
	os.remove(zip_filename)
	log_debug(f'Extracted {zip_filename} to current directory.')

# Extract the domain of all the URLs
import csv
with open(dataset_filename) as csvfile:
	reader = csv.DictReader(csvfile)
	unsafe_urls = [row['url'] for row in reader if row['type'] != 'benign']

malicious_domains = set()
for url in unsafe_urls:
	parsed_url = urlparse(url)
	domain = parsed_url.netloc
	if domain:
		malicious_domains.add(domain)

# Remove known safe domains
safe_domains = {
	'google.com', 'facebook.com', 'youtube.com', 'twitter.com', 'instagram.com',
	'linkedin.com', 'wikipedia.org', 'reddit.com', 'stackoverflow.com', 'github.com', 
}
malicious_domains = malicious_domains - safe_domains

def check_malicious_domains(urls=[]):
	# Check if the domains are malicious, using the dataset.
	# Returns True if malicious, False otherwise.
	if not urls:
		raise ValueError('No URLs provided for checking.')
	result = {}
	malicious_count = 0
	for url in urls:
		parsed_url = urlparse(url)
		domain = parsed_url.netloc
		result[url] = domain in malicious_domains
		if result[url]:
			malicious_count += 1
	return result, malicious_count


## A final function to use above functions to remove unsafe/spam URLs
def filter_urls(urls=[]):
	# Removes suspicious URLs from the list and returns a filtered list of URLs that appear safe.
	http_urls, _ = preprocess_urls(urls)
	safe_browsing_results, _ = check_google_safe_browsing(http_urls)
	malicious_domain_results, _ = check_malicious_domains(http_urls)
	filtered_urls = [url for url in http_urls \
		if not safe_browsing_results[url] and not malicious_domain_results[url]]
	removed_count = len(urls) - len(filtered_urls)
	log_info(f'Removed {removed_count}/{len(urls)} URLs that were either spam or unsafe.')
	return filtered_urls


if __name__ == '__main__':
	# Example usage
	test_urls = [
		'https://www.google.com',
		'https://www.example.com',
	]
	filtered_urls = filter_urls(test_urls)
	log_debug(f'Filtered URLs: {filtered_urls}')
