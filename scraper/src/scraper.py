import requests
import json
from bs4 import BeautifulSoup

class Scraper:
    CATEGORIES_PATH = "webapi/front/pl_PL/categories/tree"
    CATEGORY_PAGE_SUFFIX = "pl/c/{category_name}/{category_id}/{page_number}"

    def __init__(self, url):
        self.url = url

    
    @property
    def url(self):
        return self._url
    
    @url.setter
    def url(self, url):
        if requests.get(url).status_code != 200:
            raise ValueError("Failed requesting from url")
        
        self._url = url
            
        
    def parse_categories(self):
        responce = requests.get(f'{self.url}/{self.CATEGORIES_PATH}')

        if not responce:
            raise ValueError("Wrong categories path")
        
        return responce.json()