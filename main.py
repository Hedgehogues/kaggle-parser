import copy
import json
import os
import time

import bs4
import tqdm as tqdm
import requests


proxies = {}


class DataExtractor:
    def __init__(self, *, url, sc=200, ctags=2, itag=1, ignore_codes=None, rtimeout=10, retries=5):
        """
        Extract data from page of kaggle.com/*

        :param url: url of parsing
        :param sc: expected status code
        :param ctags: expected count tags with scripts
        :param itag: tag index with data
        :param ignore_codes: ignore status codes of response
        :param rtimeout: long timeout between retries
        :param retries: count retries after failed
        """
        self.__fkernel = 'push('
        self.__rkernel = ');'
        self.url = url
        self.sc = sc
        self.ctags = ctags
        self.itag = itag
        self.ignore_codes = {404} if ignore_codes is None else ignore_codes
        self.ltimeout = rtimeout
        self.retries = retries

    def __extract_info(self, *, tag):
        assert tag.contents, 'Unexpected amount contents'
        raw_text = tag.contents[0]
        raw_text = raw_text[raw_text.find(self.__fkernel) + len(self.__fkernel):-1]
        raw_text = raw_text[:raw_text.rfind(self.__rkernel)]
        return json.loads(raw_text)

    def __message(self, *, code, url):
        return f'Not {self.sc} status code. Found: {code}. Url: {url}. Ignore codes: {self.ignore_codes}'

    def __retry(self, *, url):
        i = 0
        code = None
        content = None
        while i < self.retries:
            resp = requests.get(url, proxies=proxies)
            code = resp.status_code
            if resp.status_code in self.ignore_codes:
                print(url + ' in ignore codes', flush=True)
            cond = code in self.ignore_codes or resp.status_code == self.sc
            if cond:
                content = resp.content
                break
            print('Retry timeout', flush=True)
            time.sleep(self.ltimeout)
        assert i < self.retries, self.__message(code=code, url=url)
        return content

    def __call__(self, *, path):
        """
        :param path: path of url
        :return:
        """
        content = self.__retry(url=self.url + path)
        soup = bs4.BeautifulSoup(content, 'html.parser')
        tags = soup.find_all('script', {'class': 'kaggle-component'})
        assert len(tags) == self.ctags, 'Additional script found'
        return self.__extract_info(tag=tags[self.itag])


def lb_data(_id):
    url = 'https://www.kaggle.com/c/{_id}/leaderboard.json'
    qp = {
        'includeBeforeUser': True,
        'includeAfterUser': True,
    }
    resp = requests.get(url.format(_id=_id), params=qp)
    assert resp.status_code == 200, 'Not 200 status code. Found: {resp.status_code}'
    return resp.json()


timeout = 1
url = 'https://www.kaggle.com/c/lyft-motion-prediction-autonomous-vehicles'

path_to_data = f'data/{url.split("/")[-1]}'
lb_extractor = DataExtractor(url=url)
lb_info = lb_extractor(path='/leaderboard')
_id = lb_info['competitionId']
teams = lb_data(_id=_id)
teams = teams['beforeUser'] + teams['afterUser']
user_extractor = DataExtractor(url='https://www.kaggle.com', rtimeout=10)
for t in tqdm.tqdm(teams, desc='team processing'):
    if os.path.exists(f'{path_to_data}/{t["teamId"]}.json'):
        print(f'{t["teamId"]} already exists', flush=True)
        continue
    team = copy.deepcopy(t)
    for tm in team['teamMembers']:
        user_info = user_extractor(path=tm['profileUrl'])
        tm['userInfo'] = user_info
    with open(f'{path_to_data}/{team["teamId"]}.json', 'w') as fd:
        json.dump(team, fd)
    time.sleep(timeout)
