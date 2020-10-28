import json

import requests


def flatten(*, list_):
    return [item.strip() for sublist in list_ for item in sublist]


class Builder:
    def headers(self, *, cookies):
        return {
            'cookie': '; '.join([f'{k}={v}' for k, v in cookies.items()]),
            'x-xsrf-token': cookies['XSRF-TOKEN'],
        }


class BuilderDataset(Builder):
    def body(self):
        return {
            'page': 1,
            'group': 'public',
            'size': 'all',
            'fileType': 'all',
            'license': 'all',
            'viewed': 'all',
            'categoryIds': [],
            'search': '',
            'sortBy': 'hottest',
            'userId': None,
            'competitionId': None,
            'organizationId': None,
            'maintainerOrganizationId': None, 'minSize': None, 'maxSize': None,
            'isUserQuery': False,
            'hasTasks': False,
            'topicalDataset': None,
            'includeTopicalDatasets': True,
        }


class BuilderTags(Builder):
    def body(self):
        return {
            "searchType": "dataset",
            "searchQuery": None,
            "showSystemTags": False,
            "skip": 0,
            "take": 10,
        }


def request(*, url, builder):
    __url = 'https://www.kaggle.com/datasets'
    with requests.Session() as session:
        resp = session.get(__url)
        assert resp.status_code == 200
        cookies = session.cookies.get_dict()
        payload = builder.body()
        headers = builder.headers(cookies=cookies)
        resp = session.post(url, headers=headers, data=json.dumps(payload))
    return resp.json()


url_search_datasets = 'https://www.kaggle.com/requests/SearchDatasetsRequest'
url_search_tags = 'https://www.kaggle.com/requests/SearchTagsRequest'
b = BuilderTags()
resp = request(url=url_search_tags, builder=b)
print(resp)
