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

    def get_basic_product_info(self, product):
        '''
        Extracts basic product information from the product element.
        Return: {
            "product_name": "",
            "product_link": "",
            "product_author": "",
            "price": {
                "current": "",
                "additional_info": "",
            },
            "thumbnail": "",
        }
        '''
        product_id = product.get("data-product-id", "")
        if not product_id:
            return None
        if not str(product_id).isdigit():
            return None
        product_id = int(str(product_id))
        product_info = {"price": {}}
        name_tag = product.find("a", class_="prodname")
        if name_tag:
            product_info["product_name"] = name_tag.get_text(strip=True)
            product_info["product_link"] = name_tag["href"]

        manufacturer_tag = product.find("div", class_="manufacturer")
        if manufacturer_tag:
            brand_tag = manufacturer_tag.find("a", class_="brand")
            if brand_tag:
                product_info["product_author"] = brand_tag.get_text(strip=True)

        price_tag = product.find("div", class_="price")
        if price_tag:
            em_tag = price_tag.find("em")
            if em_tag:
                product_info['price']["current"] = em_tag.get_text(strip=True)

        prod_image_link = product.find("a", class_="prodimage")
        if prod_image_link:
            img_tag = prod_image_link.find("img")
            if img_tag:
                product_info["thumbnail"] = img_tag.get("data-src", "")

        info_tag = product.find("div", class_="price__additional-info")
        if info_tag:
            product_info['price']["additional_info"] = info_tag.get_text(strip=True)
        return product_info
            

    # TODO: delivery, stock status, reviews, ratings
    def get_detailed_product_info(self, product_info):
        '''
        Fills in detailed product information into the product_info dictionary.
        Modifies product_info in place.
        Expected keys to fill:
        
        "thumbnail_high_res": "",
        "attributes": {},
        "description": "",
        "display_code": "",
        "price": {
            "regular": "",
            "omnibus": "",
        },
        "tags": [],
        '''
        if not product_info["product_link"]:
            return None
        
        product_details_url = self.url + product_info["product_link"]

        resp = requests.get(product_details_url)
        resp_bs = BeautifulSoup(resp.content, "html.parser")

        product_box = resp_bs.find("div", id="box_productfull")
        
        if product_box:
            basket_div = product_box.find("div", class_="basket")
            
            if basket_div:
                # Regular Price
                regular_price_p = basket_div.find("p", class_="price__regular")
                if regular_price_p:
                    inactive_price = regular_price_p.find("del", class_="price__inactive")
                    if inactive_price:
                        product_info['price']["regular"] = inactive_price.get_text(strip=True)

                # Omnibus / Lowest price 30 days
                omnibus_container = basket_div.find("div", class_="js__omnibus-price-container")
                if omnibus_container:
                    omnibus_price = omnibus_container.find("strong", class_="js__omnibus-price-gross")
                    if omnibus_price:
                        product_info['price']["omnibus"] = omnibus_price.get_text(strip=True)

        details_div = resp_bs.find("div", class_="maininfo")

        # High Res Image
        if details_div:
            high_res_anchor = details_div.find("a", class_="js__gallery-anchor-image")
            if high_res_anchor:
                product_info["thumbnail_high_res"] = high_res_anchor.get("href", "")

        # Display Code
        code_div = resp_bs.find("div", class_="row code")
        if code_div:
            span_tag = code_div.find("span")
            if span_tag:
                product_info["display_code"] = span_tag.get_text(strip=True)

        # Parse Attributes
        # Normalize keys to avoid duplicates (e.g., "Rok wydania" vs "rok_wydania")
        def normalize_key(k):
            return k.lower().replace(" ", "_").replace(":", "")

        # Get Meta attributes first
        meta_properties = [
            "product:rok_wydania", 
            "product:wydawnictwo", 
            "product:liczba_stron", 
            "product:wysokość", 
            "product:oprawa", 
            "product:stan_książki"
        ]
        
        product_info["attributes"] = {}
        for meta in resp_bs.find_all("meta"):
            prop = meta.get("property")
            if isinstance(prop, str) and prop in meta_properties:
                raw_key = prop.replace("product:", "")
                val = meta.get("content")
                product_info["attributes"][raw_key] = val

        # Get Table attributes (Fallback)
        data_box = resp_bs.find("div", id="box_productdata")
        if data_box:
            rows = data_box.find_all("tr")
            for row in rows:
                name_td = row.find("td", class_="name")
                val_td = row.find("td", class_="value")
                
                if name_td and val_td:
                    raw_name = name_td.get_text(strip=True)
                    clean_key = normalize_key(raw_name)
                    val = val_td.get_text(strip=True)
                    
                    # Only add if we don't already have this key from the meta tags
                    # and if the key isn't empty
                    if clean_key and clean_key not in product_info["attributes"]:
                        product_info["attributes"][clean_key] = val

        # Parse Description (with newlines)
        desc_box = resp_bs.find("div", id="box_description")
        if desc_box:
            desc_content = desc_box.find("div", itemprop="description")
            if desc_content:
                product_info["description"] = desc_content.get_text(separator="\n", strip=True)
        # Tags
        tags = []
        tags_ul = resp_bs.find("ul", class_="tags")
        if tags_ul:
            for tag_li in tags_ul.find_all("li"):
                tags.append(tag_li.get_text(strip=True))
        if tags:
            product_info["tags"] = tags
    def get_product_details(self, product):
        product_info = self.get_basic_product_info(product)
        if not product_info:
            return None
        logger.info(f"Fetching detailed info for product: {product_info.get('product_name', 'Unknown')}")
        self.get_detailed_product_info(product_info)
        return product_info

    def get_all_products_from_category(self, category, max_pages: int):
        resp = requests.get(
            self.url +
            self.CATEGORY_PAGE_SUFFIX.format(
                category_name=category['name'],
                category_id=category['id'],
                page_number=1
            )
        )
        if not resp.ok:
            raise ValueError("failed to parse category page")
        BS_data = BeautifulSoup(resp.content, "html.parser")

        products = BS_data.find_all("div", class_="product")

        for page in range(2, int(max_pages) + 1):
            resp = requests.get(
                self.url +
                self.CATEGORY_PAGE_SUFFIX.format(
                    category_name=category['name'],
                    category_id=category['id'],
                    page_number=page
                )
            )
            if not resp.ok:
                raise ValueError("failed to parse category page")
            BS_data = BeautifulSoup(resp.content, "html.parser")
            products.extend(BS_data.find_all("div", class_="product"))
            logger.info(f"Fetched page {page} for category {category['name']}")
            
        products_json = {}
        for k, product in enumerate(products):
            product_details = self.get_product_details(product)
            if product_details:
                product_id = product.get("data-product-id", "")
                products_json[product_id] = product_details

        return products_json

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
                products = self.get_all_products_from_category(cat, cat["number_of_pages"])

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

