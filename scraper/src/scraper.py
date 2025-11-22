import requests
import regex
import json
from slugify import slugify
from bs4 import BeautifulSoup
import logging_config
import logging

logging_config.setup_logging()
logger = logging.getLogger(__name__)

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
            
        
    def parse_categories(self, parse_pages=True):
        response = requests.get(f'{self.url}/{self.CATEGORIES_PATH}')

        if not response.ok:
            raise ValueError("Wrong categories path")
        
        # A list of dictionaries 
        self.tree = response.json()

        if parse_pages:
            self.parse_number_of_pages_rec(self.tree)

    def parse_number_of_pages_rec(self, categories):
        for cat in categories:
            sub_cats = cat["children"]

            # If category has children, go deeper
            if len(sub_cats) != 0:
                self.parse_number_of_pages_rec(sub_cats)
            else:
                # If has no children, we count pages
                logger.info(f"Count pages for {cat['name']} (id: {cat['id']})")

                cat["number_of_pages"] = self.parse_number_of_pages(cat)

    def get_all_products_from_category(self, category, max_pages=None):
        ...

    def parse_products(self, categories=None):
        if not categories:
            categories = self.tree

        for cat in categories:
            sub_cats = cat["children"]

            # If category has children, go deeper
            if len(sub_cats) != 0:
                self.parse_products(sub_cats)
            else:
                # If has no children, we parse products for category
                logger.info(f"Parsing products for {cat['name']} (id: {cat['id']})")

                cat["number_of_pages"] = self.parse_number_of_pages(cat)
                self.get_all_products_from_category(cat)

    def parse_products_from_category(self, category):
        max_page = category["number_of_pages"]

        for i in range(max_page):
            category["children"].append(self.parse_products_from_page(category, i))

    def parse_products_from_page(self, category, page_n):
        category_name = self.clean_for_url(category['name'])
        suffix = self.CATEGORY_PAGE_SUFFIX.format(category_name=category_name, category_id=category['id'], page_number=page_n)
        
        print(f"{self.url}/{suffix}")

        response = requests.get(f"{self.url}/{suffix}")

        if not response.ok:
            # Will it return 404, or just a blank page?
            raise ValueError("failed to parse category page")
        
        # Example output, will be replaced with html parser
        return [f"a{page_n}", f"b{page_n}", f"c{page_n}"]


    def parse_number_of_pages(self, category):
        suffix = self.CATEGORY_PAGE_SUFFIX.format(category_name=category['name'], category_id=category['id'], page_number=1)
        
        response = requests.get(f"{self.url}/{suffix}")

        if not response.ok:
            raise ValueError("pages are over or the suffix is incorrect")
        
        # parse all the <li> elements from <ui class="selected">
        # get elements[-1] value
        soup = BeautifulSoup(response.text, 'html.parser')
        paginator = soup.find("ul", class_="paginator")

        if not paginator:
            # If category has only one page, there will be no paginator
            return 1

        # (?r) flag searches from the end of string
        max_page = regex.search(r"(?r)(\d+)", paginator.text).group()

        return int(max_page)


    def clean_for_url(self, cat_name):
        return slugify(cat_name).capitalize()
    
    def save_tree(self, path="results.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.tree, f, ensure_ascii=False, indent=4)

    def load_tree(self, path="results.json"):
        with open(path, "r", encoding="utf-8") as f:
            self.tree = json.load(f)

