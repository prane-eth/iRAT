from irat.utils.settings import Settings

from googleapiclient.discovery import build


class GoogleSearch(object):
	def __init__(self, max_fetch_results = None):
		api_key = Settings.get("GOOGLE_API_KEY")
		self.CX = Settings.get("GOOGLE_PROGRAMMABLE_SEARCH_ENGINE_ID_CX")
		self.service = build("customsearch", "v1", developerKey=api_key)

		if max_fetch_results:
			self.max_fetch_results = max_fetch_results
		else:
			self.max_fetch_results = Settings.get("SCRAPER_MAX_FETCH_RESULTS")
			self.max_fetch_results = int(self.max_fetch_results)
	
	def search(self, query: str, **kwargs):
		res = self.service.cse().list(q=query, cx=self.CX, **kwargs).execute()
		return res

	def run_query(self, query: str) -> list[str]:
		# Perform a Google search using the provided query and return a list of URLs.
		res_data = self.search(query)
		total_results = int(res_data.get("searchInformation", {}).get("totalResults", 0))
		# return res_data if total_results else None
		if not total_results:
			return []
		items = res_data.get("items", [])
		if not items:
			return []
		# Limit the number of results to max_fetch_results
		items = items[:self.max_fetch_results]
		# Extract URLs from the items
		urls = [item.get("link") for item in items if item.get("link")]
		return urls if urls else []

