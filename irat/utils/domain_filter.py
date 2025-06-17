from irat.utils.logger import log_debug, log_info
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
	# remove URLs with protocols other than http and https
	http_urls = [url for url in urls if url.startswith(('http://', 'https://'))]
	# # convert http to https
	# http_urls = [url.replace('http://', 'https://') for url in http_urls]
	
	# if the page uses an IP address instead of a domain name, remove it
	http_urls = [url for url in http_urls if not _is_ip_address(url)]

	removed_count = len(urls) - len(http_urls)

	return http_urls, removed_count


### Using Google Safe Browsing API

from pysafebrowsing import SafeBrowsing

GOOGLE_API_KEY = env('GOOGLE_API_KEY')
safebrowsing = SafeBrowsing(GOOGLE_API_KEY)

def check_google_safe_browsing(urls=[]):
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


### Use Kaggle dataset

import requests
import os

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

import csv
with open(dataset_filename) as csvfile:
	reader = csv.DictReader(csvfile)
	unsafe_urls = [row['url'] for row in reader if row['type'] != 'benign']

# get the domain of all the URLs
malicious_domains = set()
for url in unsafe_urls:
	parsed_url = urlparse(url)
	domain = parsed_url.netloc
	if domain:
		malicious_domains.add(domain)

# remove safe domains
safe_domains = {
	'google.com', 'facebook.com', 'youtube.com', 'twitter.com', 'instagram.com',
	'linkedin.com', 'wikipedia.org', 'reddit.com', 'pinterest.com', 'tumblr.com'
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
	# removed_urls = set(urls) - set(filtered_urls)
	removed_count = len(urls) - len(filtered_urls)
	log_info(f'Removed {removed_count}/{len(urls)} URLs that were either malicious/unsafe.')
	return filtered_urls
