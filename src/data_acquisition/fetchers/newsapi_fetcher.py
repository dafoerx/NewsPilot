'''
Author: WangQiushuo 185886867@qq.com
Date: 2025-12-23 21:59:45
LastEditors: WangQiushuo 185886867@qq.com
LastEditTime: 2025-12-24 23:23:36
FilePath: \NewsPilot\src\data_acquisition\fetchers\newsapi_fetcher.py
Description: 

Copyright (c) 2025 by , All Rights Reserved. 
'''
from newsapi import NewsApiClient
import json
import time


keys = json.load(open('keys.json'))
newsapi = NewsApiClient(api_key=keys['newsapi'])

CATEGORYS = ['business', 'science', 'technology']
SOURCES = [
    "reuters", "bloomberg", "the-wall-street-journal", 
    "associated-press", "axios", "fortune", "xinhua-net"
]

all_headlines = {
    "status": "ok",
    "totalResults": 0,
    "articles": []
}

for category in CATEGORYS:
    top_headlines = newsapi.get_top_headlines(category=category)
    print(category)
    time.sleep(1)
    if top_headlines['status'] == 'ok':
        all_headlines['articles'].extend(top_headlines['articles'])
top_headlines = newsapi.get_top_headlines(sources=",".join(SOURCES))
print("sources")
time.sleep(1)
if top_headlines['status'] == 'ok':
    all_headlines['articles'].extend(top_headlines['articles'])

all_headlines['totalResults'] = len(all_headlines['articles'])
for new in all_headlines['articles']:
    new['content'] =  ''
    

json.dump(all_headlines, open('top_headlines.json', 'w'), indent=4)