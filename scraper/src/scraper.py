import requests
import regex
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
        if not requests.get(url).ok:
            raise ValueError("Failed requesting from url")
        
        self._url = url
            
        
    def parse_categories(self):
        response = requests.get(f'{self.url}/{self.CATEGORIES_PATH}')

        if not response.ok:
            raise ValueError("Wrong categories path")
        
        # A list of dictionaries 
        self.tree = response.json()


    def parse_products(self, debug=False):
        for cat in self.tree:
            for sub_cat in cat['children']:
                page_n = 1

                max_page = self.parse_number_of_pages(sub_cat)
                
                # Assign new atribute to category
                sub_cat["number_of_pages"] = max_page

                # Will be assigned as sub_cat['children']
                cat_products = []

                while True:
                    try:
                        cat_products.append(self.parse_products_from_page(sub_cat, page_n))
                        
                        if debug:
                            print(f"{sub_cat['name']}: page {page_n}")

                        page_n += 1
                    except ValueError:
                        # Will be raised if pages are over
                        break
                
                # Assign products to category
                sub_cat['children'] = cat_products

    def parse_number_of_pages(self, category):
        suffix = self.CATEGORY_PAGE_SUFFIX.format(category_name=category['name'], category_id=category['id'], page_number=1)
        
        response = requests.get(f"{self.url}/{suffix}")

        if not response.ok:
            raise ValueError("pages are over or the suffix is incorrect")
        
        # parse all the <li> elements from <ui class="selected">
        # get elements[-1] value
        soup = BeautifulSoup(response.text, 'html.parser')
        paginator = soup.find("ul", class_="paginator")

        # (?r) flag searches from the end of string
        max_page = regex.search(r"(?r)(\d+)", paginator.text).group()

        return int(max_page)
    
    def parse_products_from_page(self, category, page_n):
        suffix = self.CATEGORY_PAGE_SUFFIX.format(category_name=category['name'], category_id=category['id'], page_number=page_n)
        
        response = requests.get(f"{self.url}/{suffix}")

        if (not response.ok) or (page_n > category['number_of_pages']):
            raise ValueError("pages are over or the suffix is incorrect")
        
        # Example output, will be replaced with html parser
        return [f"a{page_n}", f"b{page_n}", f"c{page_n}"]

    