import requests
import regex
import json
from slugify import slugify
from bs4 import BeautifulSoup
import logging_config
import logging
import copy
from math import ceil

logging_config.setup_logging()
logger = logging.getLogger(__name__)

class Scraper:
    CATEGORIES_PATH = "/webapi/front/pl_PL/categories/tree"
    CATEGORY_PAGE_SUFFIX = "/pl/c/{category_name}/{category_id}/{page_number}"

    def __init__(self, url, crop=False, n_cats=None, n_subcats=None, n_layers=None, n_products=None):
        '''
        Initializes a parser object to collect data 
        about categories tree and each product in them from the url.

        Parameters:
            url         web shop to parse from (required attibute),

            crop        optional flag to crop categories tree for
                        specific number of categories and products only 
                            (if True, all the attributes below are required),
            
            n_cats      number of top-level categories
            n_subcats   number of subcategories for each layer
            n_layers    number of subcategores layers, for example:
                            1 == "only top level has sub-categories"
                            2 == "each subcategory of top level also has subcategories"
            n_products  maximum number of products to parse
        '''

        self.url = url

        # List of references for each leaf category
        self.leaf_cats = []
        
        self.products_per_page = None

        # List of dictionaries. TODO: add save to json method
        self.products = []

        if crop:
            self.crop = crop
            self.n_cats = n_cats
            self.n_subcats = n_subcats
            self.n_layers = n_layers
            self.n_products = n_products

    
    @property
    def url(self):
        return self._url
    
    @url.setter
    def url(self, url):
        if not requests.get(url).ok:
            raise ValueError("Failed requesting from url")
        self._url = url
            

    @property
    def n_cats(self):
        return self._n_cats
    
    @n_cats.setter
    def n_cats(self, n_cats):
        if not n_cats or type(n_cats) != int or n_cats <= 0:
            raise ValueError("n_cats must be defined")
        self._n_cats = n_cats


    @property
    def n_subcats(self):
        return self._n_subcats
    
    @n_subcats.setter
    def n_subcats(self, n_subcats):
        if not n_subcats or type(n_subcats) != int or n_subcats <= 0:
            raise ValueError("n_subcats must be defined")
        self._n_subcats = n_subcats


    @property
    def n_layers(self):
        return self._n_layers
    
    @n_layers.setter
    def n_layers(self, n_layers):
        if not n_layers or type(n_layers) != int or n_layers <= 0:
            raise ValueError("n_layers must be defined")
        self._n_layers = n_layers


    @property
    def n_products(self):
        return self._n_products
    
    @n_products.setter
    def n_products(self, n_products):
        if not n_products or type(n_products) != int or n_products <= 0:
            raise ValueError("n_products must be defined")
        self._n_products = n_products

            
        
    def parse_categories(self, parse_pages=True):
        response = requests.get(f'{self.url}{self.CATEGORIES_PATH}')

        if not response.ok:
            raise ValueError("Wrong categories path")
        
        # A list of dictionaries 
        self.tree = response.json()

        if self.crop:
            self.tree = self.crop_categories_tree()

        if parse_pages:
            self.parse_number_of_pages_rec(self.tree)

        if self.crop:
            self.crop_pages()

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

                # Append a reference to this category to leaf categories list
                self.leaf_cats.append(cat)

    def parse_number_of_pages(self, category):
        suffix = self.CATEGORY_PAGE_SUFFIX.format(category_name=category['name'], category_id=category['id'], page_number=1)
        
        response = requests.get(f"{self.url}{suffix}")

        if not response.ok:
            raise ValueError("pages are over or the suffix is incorrect")
        
        # parse all the <li> elements from <ui class="selected">
        soup = BeautifulSoup(response.text, 'html.parser')
        paginator = soup.find("ul", class_="paginator")

        if not paginator:
            # If category has only one page, there will be no paginator
            return 1

        # (?r) flag searches from the end of string
        max_page = regex.search(r"(?r)(\d+)", paginator.text).group()

        # Parse number of products per page once for the whole website, 
        # but the page must be full
        if (not self.products_per_page) and (int(max_page) > 1):
            self.products_per_page = self.parse_products_per_page(soup)

        return int(max_page)
    
    def parse_products_per_page(self, soup):
        return len(soup.find_all("div", class_="product"))



    def crop_categories_tree(self):
        '''
        Returns a cropped tree, but does not assign it automatically

        Crops categories tree 
        so it fits requrements 
        using class parameters:
            n_cats,
            n_subcats,
            n_layers
        '''
        
        logger.info("--- Started cropping categories tree ---")

        # Copies first n_cats categories
        cropped_tree = copy.deepcopy(self.tree[:self.n_cats])

        def crop_subcategories(current_layer, layers_left):
            # Only first n_subcats for each category stay
            for cat in current_layer:
                if layers_left <= 0:
                    # This was the last layer, so trim any further layers and stop
                    cat['children'] = []
                    logger.info(f"Remove children for {cat['name']} (id: {cat['id']})")
                else:
                    logger.info(f"Crop subcategories for {cat['name']} (id: {cat['id']})")
                    cat['children'] = cat['children'][:self.n_subcats]
                    crop_subcategories(cat['children'], layers_left - 1)

        crop_subcategories(cropped_tree, self.n_layers)       

        logger.info("--- Categories tree has been cropped successfully! ---")
        return cropped_tree
    
    def crop_pages(self):
        '''
        Crops page numbers for each leaf category
        based on n_products parameter
        '''

        logger.info("--- Started cropping numbers of pages ---")
        logger.info(f"Number of products per page: {self.products_per_page}")


        # Sort leaf categories by number of pages in the ascending order
        self.leaf_cats.sort(key=lambda x: x['number_of_pages'])
        
        # In perfect world each category should contain exactly that much products
        optimal_products_per_cat = self.n_products / len(self.leaf_cats)
        
        # Round up to be sure that products requirement will be satisfied
        optimal_pages_per_cat = ceil(optimal_products_per_cat/self.products_per_page)
        
        # If there is not enough pages in category, the debt is increased.
        pages_debt = 0

        # For debug purpouse
        products_estimated = 0

        # Iterate through them and try to achieve perfect pages distribution
        for cat in self.leaf_cats:
            # Substract one to be sure that every page is full
            pages = cat['number_of_pages'] - 1

            if pages > optimal_pages_per_cat:
                pages_gain = 0

                if pages_debt:
                    # Gain cannot be higher than debt
                    pages_gain = min(pages - optimal_pages_per_cat, pages_debt)
                    pages_debt -= pages_gain

                cat['number_of_pages'] = optimal_pages_per_cat + pages_gain
            else:
                # There is not enough pages, so the debt is increased and number of pages is unchanged
                pages_debt += optimal_pages_per_cat - pages

            products_estimated += cat['number_of_pages'] * self.products_per_page

        if pages_debt:
            logger.error(f"There is not enough products in a cropped categories")

        logger.info(f"Finishing cropping pages. Estimated number of products ~{products_estimated}")

        logger.info("--- Numbers of pages have been cropped successfully! ---")



    def parse_products(self):
        logger.info("--- Started parsing products ---")

        for cat in self.leaf_cats:
            # If has no children, we parse products for category
            logger.info(f"Parsing products for {cat['name']} (id: {cat['id']})")

            # Add products from category to parsed products
            self.products.extend(self.parse_products_from_category(cat))

        logger.info(f"--- Parsed {len(self.products)} products ---")

    def parse_products_from_category(self, category):
        max_page = category["number_of_pages"]
        products = []

        for i in range(max_page):
            products.extend(self.parse_products_from_page(category, i + 1))

        products_full_info = []

        for _, product in enumerate(products):
            product_details, product_id = self.parse_product_details(product)
            if product_details:
                product_details['id'] = product_id
                product_details['category_id'] = category['id']
                products_full_info.append(product_details)

        return products_full_info

    def parse_products_from_page(self, category, page_n):
        category_name = self.clean_for_url(category['name'])
        suffix = self.CATEGORY_PAGE_SUFFIX.format(category_name=category_name, category_id=category['id'], page_number=page_n)

        response = requests.get(f"{self.url}{suffix}")

        if not response.ok:
            raise ValueError("failed to parse category page")
    
        BS_data = BeautifulSoup(response.content, "html.parser")
        products = BS_data.find_all("div", class_="product")
        logger.info(f"Fetched page {page_n} for category {category['name']}")

        return products

    def parse_product_details(self, product):
        product_info, product_id = self.parse_basic_product_info(product)
        if not product_info:
            return None, None
        logger.info(f"Fetching detailed info for product: {product_info.get('product_name', 'Unknown')}")
        self.parse_detailed_product_info(product_info)
        return product_info, product_id

    def parse_basic_product_info(self, product):
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
            logger.warning("Product without product id found, skipping...")
            return None, None
        if not str(product_id).isdigit():
            logger.warning("Product with invalid product id found, skipping...")
            return None, None
        product_id = int(str(product_id))
        product_info = {"price": {}}
        name_tag = product.find("a", class_="prodname")
        if name_tag:
            product_info["product_name"] = name_tag.get_text(strip=True)
            product_info["product_link"] = name_tag["href"]
        else:
            logger.warning(f"Product with id {product_id} has no name tag, skipping...")

        manufacturer_tag = product.find("div", class_="manufacturer")
        if manufacturer_tag:
            brand_tag = manufacturer_tag.find("a", class_="brand")
            if brand_tag:
                product_info["product_author"] = brand_tag.get_text(strip=True)
            else:
                logger.warning(f"Product with id {product_id} has no brand tag.")
        else:
            logger.warning(f"Product with id {product_id} has no manufacturer tag.")

        price_tag = product.find("div", class_="price")
        if price_tag:
            em_tag = price_tag.find("em")
            if em_tag:
                product_info['price']["current"] = em_tag.get_text(strip=True)
            else:
                logger.warning(f"Product with id {product_id} has no price em tag.")
        else:
            logger.warning(f"Product with id {product_id} has no price tag.")

        prod_image_link = product.find("a", class_="prodimage")
        if prod_image_link:
            img_tag = prod_image_link.find("img")
            if img_tag:
                product_info["thumbnail"] = img_tag.get("data-src", "")
            else:
                logger.warning(f"Product with id {product_id} has no image tag.")
        else:
            logger.warning(f"Product with id {product_id} has no prodimage tag.")

        info_tag = product.find("div", class_="price__additional-info")
        if info_tag:
            product_info['price']["additional_info"] = info_tag.get_text(strip=True)
        return product_info, product_id
        
    def parse_detailed_product_info(self, product_info):
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
        "shipping_info": {},
        '''
        if not product_info.get("product_link"):
            logger.warning("No product link found for detailed info parsing.")
            return
        
        product_details_url = self.url + product_info["product_link"]

        try:
            resp = requests.get(product_details_url)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch product details from {product_details_url}: {e}")
            return
            
        resp_bs = BeautifulSoup(resp.content, "html.parser")

        price = product_info['price'].get("current", "").replace(' zł', '').replace(',', '.')
        stock_input = resp_bs.find('input', {'name': 'stock_id'})
        if not stock_input:
            logger.error("No stock_id input found on product details page.")
            return
        
        stock_id = stock_input.get('value')
        api_url = f"{self.url}/product/getstockcostinfo/stock/{stock_id}/price/{price}"

        try:
            resp = requests.get(
                api_url
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch stock and cost info from {api_url}: {e}")
            return

        stock_data = resp.json()
        product_info["shipping_info"] = stock_data

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
            else:
                logger.warning("No high res image anchor found.")
        else:
            logger.warning("No maininfo div found.")

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
            
    

    def parse_sample_images(self, n_images):
        if not self.products:
            raise ValueError("Products are required for image")
        
        self.images_bin = []

        logger.info(f"--- Started parsing {n_images} sample images ---")

        # Loop variables
        n_products = len(self.products)
        parsed = 0
        # Index var starts from -1 since it will be incremented immediately
        i = -1

        while parsed < n_images and i < n_products:
            i += 1
            
            resp = requests.get(f"{self.url}{self.products[i]["thumbnail_high_res"]}")

            if not resp.ok:
                logger.error(f"Failed to parse high-res image for product (id: {self.products[i]["id"]}), skipping it...")
                continue
                    
            logger.info(f"Parsed high-res image for product (id: {self.products[i]["id"]})")

            # Raw binary data is contained inside resp.content
            self.images_bin.append(resp.content)
            parsed += 1

        logger.info(f"--- Parsed {len(self.images_bin)} images ---")


    def clean_for_url(self, cat_name):
        return slugify(cat_name).capitalize()
    
    def save_tree(self, path="categories.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.tree, f, ensure_ascii=False, indent=4)
            logger.info(f"Categories tree has been saved to {path}")

    def load_tree(self, path="categories.json"):
        with open(path, "r", encoding="utf-8") as f:
            self.tree = json.load(f)
            logger.info(f"Categories tree has been load from {path}")

    def save_products(self, path="products.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.products, f, ensure_ascii=False, indent=4)
            logger.info(f"Products have been saved to {path}")
        
    def load_products(self, path="products.json"):
        with open(path, "r", encoding="utf-8") as f:
            self.products = json.load(f)
            logger.info(f"Products have been load from {path}")


