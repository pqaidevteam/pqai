import requests
from config.config import extensions as EXTENSIONS

HTTP_SUCCESS = 200

def search_extensions (search_params):
	results = [search_extension(host, search_params)
			for extension in EXTENSIONS]
	return merge(results)


def search_extension (host, search_params):
	url = f'{host}/extension'
	response = requests.get(url, search_params)
	if response.status_code != HTTP_SUCCESS:
		print(f'Error in getting data from extension {host}')
		return []
	return response.json().results


def merge (results_lists):
	return _deduplicate(
			_sort_by_score(
			 _flatten(results_lists)))


def _sort_by_score (results):
	return sorted(results, key=lambda x: x['score'])


def _flatten (arr):
	return [res for results in arr for res in results]


def _deduplicate (arr):
	if len(arr) == 0:
		return arr
	deduplicated = [arr[0]]
	for current in arr[1:]:
		previous = deduplicated[-1]
		if current['abstract'] != previous['abstract']:
			deduplicated.append(current)
	return deduplicated
