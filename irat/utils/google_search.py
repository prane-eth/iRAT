from irat.utils.logger import log_error, log_info
from irat.utils.settings import Settings, set_env, env

from googleapiclient.discovery import build

GOOGLE_API_KEYS = env("GOOGLE_API_KEYS")  # Keys of all members of the team.
GOOGLE_API_KEYS = [key.strip() for key in GOOGLE_API_KEYS.split(",") if key.strip() and '#' not in key]
if not GOOGLE_API_KEYS:
	raise ValueError("Google API key is not set in the settings.")


class GoogleSearch(object):
	def __init__(self, max_fetch_results = None):
		self.CX = Settings.get("GOOGLE_PROGRAMMABLE_SEARCH_ENGINE_ID_CX")

		set_env("GOOGLE_API_KEY", GOOGLE_API_KEYS[0])
		self.service = build("customsearch", "v1", developerKey=GOOGLE_API_KEYS[0])

		if max_fetch_results:
			self.max_fetch_results = max_fetch_results
		else:
			self.max_fetch_results = Settings.get("SCRAPER_MAX_FETCH_RESULTS")
			self.max_fetch_results = int(self.max_fetch_results)

	def change_api_key(self):
		if not GOOGLE_API_KEYS:
			log_error("Google Search: No more API keys available. Exiting.")
			with open("error.txt", "w") as file:
				file.write("Error 429: No more API keys available.")
			raise Exception("Error 429: No more API keys available.")

		# Switch to the next API key in the list.
		first_key = GOOGLE_API_KEYS.pop(0)
		with open("removed_keys.txt", "a") as file:
			file.write(first_key + '\n')
		# Remove the current API key from the list
		log_info(f"\nGoogle Search: Rate limit exceeded with key: ....{first_key[-3:]} \n\n")

		if not GOOGLE_API_KEYS:
			log_error("Google Search: No more API keys available. Exiting.")
			with open("error.txt", "w") as file:
				file.write("Error 429: No more API keys available.")
			raise Exception("Error 429: No more API keys available.")

		set_env("GOOGLE_API_KEY", GOOGLE_API_KEYS[0])
		self.service = build("customsearch", "v1", developerKey=GOOGLE_API_KEYS[0])

	def search(self, query: str, **kwargs):
		res = self.service.cse().list(q=query, cx=self.CX, **kwargs).execute()
		return res

	def run_query(self, query: str) -> list[str]:
		try:
			# Perform a Google search using the provided query and return a list of URLs.
			res_data = self.search(query)
			total_results = int(res_data.get("searchInformation", {}).get("totalResults", 0))
			# return res_data if total_results else None
			if not total_results:
				log_info("Google Search: Fetched results successfully: 0 results")
				return []
			items = res_data.get("items", [])
			if not items:
				log_info("Google Search: Fetched results successfully: 0 items")
				return []
			# Limit the number of results to max_fetch_results
			items = items[:self.max_fetch_results]
			# Extract URLs from the items
			urls = [item.get("link") for item in items if item.get("link")]
			log_info("Google Search: Fetched results successfully:", len(urls), "URLs")
			return urls or []
		except Exception as e:
			if "429" in str(e):
				self.change_api_key()
				return self.run_query(query)
			else:
				log_error(f"Google Search Error: {e}".split('key=')[0])
				raise e


if __name__ == "__main__":
	# Test the code
	try:
		query = "Python programming language"
		google_searcher = GoogleSearch(max_fetch_results=1)
		results = google_searcher.run_query(query)
		print("Search results for query:", query)
		for url in results:
			print(url)
	except Exception as e:
		log_error(f"An error occurred during Google search: {e}")
		raise e
