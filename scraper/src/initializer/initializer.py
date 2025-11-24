import requests
import json
import sys
import os
import logging
from typing import Dict, List, Optional, Any

# Add parent directory to path to import logging_config from scraper/src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging_config

logging_config.setup_logging()
logger = logging.getLogger(__name__)


class Initializer:
    '''
    Initializer class that collects data about categories and products 
    from scraper results and sends them to Prestashop 1.7.8 using REST API webservice.
    
    This class handles:
    - Loading categories and products from JSON files
    - Authentication with Prestashop API
    - Creating categories and products in the Prestashop store
    '''

    def __init__(self, api_url, api_key, categories_path="scraper/results/categories.json", 
                 products_path="scraper/results/products.json"):
        '''
        Initializes the Initializer object for Prestashop API communication.

        Parameters:
            api_url         URL of Prestashop REST API endpoint (required),
            api_key         API key for Prestashop authentication (required),
            categories_path path to categories.json file from scraper results,
            products_path   path to products.json file from scraper results
        '''

        self.api_url = api_url
        self.api_key = api_key
        self.categories_path = categories_path
        self.products_path = products_path

        # Store loaded data
        self.categories = []
        self.products = []
        
        # Map old category IDs to new Prestashop category IDs
        self.category_id_map = {}

        # Track API operations
        self.created_categories = []
        self.created_products = []
        self.failed_operations = []


    @property
    def api_url(self):
        return self._api_url
    
    @api_url.setter
    def api_url(self, api_url):
        if not api_url or type(api_url) != str or not api_url.strip():
            raise ValueError("api_url must be a non-empty string")
        self._api_url = api_url.rstrip('/')


    @property
    def api_key(self):
        return self._api_key
    
    @api_key.setter
    def api_key(self, api_key):
        if not api_key or type(api_key) != str or not api_key.strip():
            raise ValueError("api_key must be a non-empty string")
        self._api_key = api_key


    @property
    def categories_path(self):
        return self._categories_path
    
    @categories_path.setter
    def categories_path(self, categories_path):
        if not categories_path or type(categories_path) != str or not categories_path.strip():
            raise ValueError("categories_path must be a non-empty string")
        self._categories_path = categories_path


    @property
    def products_path(self):
        return self._products_path
    
    @products_path.setter
    def products_path(self, products_path):
        if not products_path or type(products_path) != str or not products_path.strip():
            raise ValueError("products_path must be a non-empty string")
        self._products_path = products_path


    def get_auth_headers(self) -> Dict[str, str]:
        '''
        Returns authentication headers for Prestashop API requests.
        
        Returns:
            Dictionary with authorization header
        '''
        return {
            "Content-Type": "application/xml",
            "Accept": "application/json"
        }


    def test_connection(self) -> bool:
        '''
        Tests the connection to Prestashop API.
        
        Returns:
            True if connection successful, False otherwise
        '''
        try:
            response = requests.get(
                f"{self.api_url}/categories",
                params={"ws_key": self.api_key, "output_format": "JSON"},
                headers=self.get_auth_headers(),
                timeout=10,
                verify=False
            )
            
            if response.ok:
                logger.info("Successfully connected to Prestashop API")
                return True
            else:
                logger.error(f"Failed to connect to Prestashop API. Status code: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Connection error to Prestashop API: {e}")
            return False


    def load_categories(self) -> bool:
        '''
        Loads categories from JSON file.
        
        Returns:
            True if loaded successfully, False otherwise
        '''
        try:
            with open(self.categories_path, "r", encoding="utf-8") as f:
                self.categories = json.load(f)
                logger.info(f"Loaded {len(self.categories)} top-level categories from {self.categories_path}")
                return True
                
        except FileNotFoundError:
            logger.error(f"Categories file not found: {self.categories_path}")
            return False
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in categories file: {self.categories_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to load categories: {e}")
            return False


    def load_products(self) -> bool:
        '''
        Loads products from JSON file.
        
        Returns:
            True if loaded successfully, False otherwise
        '''
        try:
            with open(self.products_path, "r", encoding="utf-8") as f:
                self.products = json.load(f)
                logger.info(f"Loaded {len(self.products)} products from {self.products_path}")
                return True
                
        except FileNotFoundError:
            logger.error(f"Products file not found: {self.products_path}")
            return False
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in products file: {self.products_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to load products: {e}")
            return False


    def flatten_categories(self, categories: List[Dict], parent_id: int = 0) -> List[Dict]:
        '''
        Flattens nested categories tree into a list of dictionaries 
        with parent information for hierarchical creation.

        Parameters:
            categories  list of category dictionaries (potentially nested)
            parent_id   ID of parent category in Prestashop (0 for root)

        Returns:
            Flattened list of categories with parent_id information
        '''
        flattened = []
        
        for cat in categories:
            cat_copy = {
                "source_id": cat["id"],
                "name": cat["name"],
                "parent_id": parent_id
            }
            flattened.append(cat_copy)
            
            # Recursively flatten children
            if cat.get("children"):
                # Note: parent_id will be set after this category is created in Prestashop
                child_flattened = self.flatten_categories(cat["children"], parent_id=cat["id"])
                flattened.extend(child_flattened)
        
        return flattened


    def create_category(self, category: Dict, parent_id: int = 0) -> Optional[int]:
        '''
        Creates a single category in Prestashop.

        Parameters:
            category    dictionary with category data
            parent_id   ID of parent category in Prestashop (0 for root)

        Returns:
            New Prestashop category ID if successful, None otherwise
        '''
        try:
            # Build XML payload - PrestaShop requires XML in request body, but returns JSON
            xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<prestashop>
    <category>
        <name>{category.get("name")}</name>
        <link_rewrite>{self._slugify(category.get("name", ""))}</link_rewrite>
        <active>1</active>
        <id_parent>{parent_id}</id_parent>
    </category>
</prestashop>"""
            
            response = requests.post(
                f"{self.api_url}/categories",
                params={"ws_key": self.api_key, "output_format": "JSON"},
                data=xml_payload.encode('utf-8'),
                headers=self.get_auth_headers(),
                timeout=10,
                verify=False
            )
            
            logger.info(f"POST {self.api_url}/categories - Status: {response.status_code}, Headers: {dict(response.headers)}, Body: {response.text[:200]}")
            
            if response.ok:
                if response.text:
                    try:
                        response_data = response.json()
                        prestashop_id = response_data.get("category", {}).get("id")
                        if not prestashop_id:
                            logger.warning(f"No ID in response for category '{category.get('name')}'")
                            prestashop_id = 1
                    except Exception as parse_err:
                        logger.warning(f"Could not parse response for category '{category.get('name')}': {parse_err}")
                        prestashop_id = 1
                else:
                    logger.warning(f"Empty response body for category '{category.get('name')}', using dummy ID")
                    prestashop_id = 1
                    
                source_id = category.get("source_id")
                
                # Store mapping between source and Prestashop IDs
                if source_id:
                    self.category_id_map[source_id] = prestashop_id
                
                logger.info(f"Created category '{category.get('name')}' (source_id: {source_id}, prestashop_id: {prestashop_id})")
                self.created_categories.append(prestashop_id)
                return prestashop_id
            else:
                logger.error(f"Failed to create category '{category.get('name')}'. Status: {response.status_code}. Response: {response.text}")
                self.failed_operations.append({
                    "type": "category",
                    "data": category,
                    "status_code": response.status_code,
                    "error": response.text
                })
                return None
                
        except Exception as e:
            logger.error(f"Error while creating category '{category.get('name')}': {type(e).__name__}: {e}")
            self.failed_operations.append({
                "type": "category",
                "data": category,
                "error": str(e)
            })
            return None


    def _slugify(self, text: str) -> str:
        '''
        Simple slugify function to create URL-friendly names.
        
        Parameters:
            text input text to slugify
            
        Returns:
            Slugified text
        '''
        import re
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')


    def create_categories(self) -> bool:
        '''
        Creates all categories in Prestashop maintaining the hierarchical structure.
        
        Returns:
            True if all categories created successfully, False otherwise
        '''
        if not self.categories:
            logger.warning("No categories to create. Load categories first.")
            return False
        
        logger.info("--- Started creating categories ---")
        
        # First pass: create root-level categories
        root_categories = self.categories
        
        def create_categories_recursive(cats: List[Dict], parent_id: int = 0) -> bool:
            '''Recursively creates categories maintaining hierarchy'''
            all_success = True
            
            for cat in cats:
                prestashop_id = self.create_category(cat, parent_id)
                
                if prestashop_id is None:
                    all_success = False
                    # Continue with other categories even if one fails
                    continue
                
                # Recursively create children
                if cat.get("children"):
                    child_success = create_categories_recursive(cat["children"], prestashop_id)
                    if not child_success:
                        all_success = False
            
            return all_success
        
        success = create_categories_recursive(root_categories)
        
        if success:
            logger.info(f"--- Successfully created {len(self.created_categories)} categories ---")
        else:
            logger.warning(f"--- Created {len(self.created_categories)} categories with {len(self.failed_operations)} failures ---")
        
        return success


    def create_product(self, product: Dict) -> Optional[int]:
        '''
        Creates a single product in Prestashop.

        Parameters:
            product dictionary with product data from scraper

        Returns:
            New Prestashop product ID if successful, None otherwise
        '''
        try:
            # Get Prestashop category ID from mapping
            source_category_id = product.get("category_id")
            prestashop_category_id = self.category_id_map.get(source_category_id)
            
            if not prestashop_category_id:
                logger.warning(f"No category mapping found for product '{product.get('product_name')}'. Skipping...")
                self.failed_operations.append({
                    "type": "product",
                    "data": product,
                    "error": "Category mapping not found"
                })
                return None
            
            # Parse price
            price_str = product.get("price", {}).get("current", "0").replace(" zł", "").replace(",", ".")
            try:
                price = float(price_str) if price_str else 0.0
            except ValueError:
                price = 0.0
            
            # Build product description from available fields
            description = self._build_product_description(product)
            
            # Escape XML special characters
            def escape_xml(text):
                if not text:
                    return ""
                return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;").replace("'", "&apos;")
            
            # Build XML payload for Prestashop REST API
            xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<prestashop>
    <product>
        <name>{escape_xml(product.get("product_name", "Unknown"))}</name>
        <description_short>{escape_xml(description[:200] if description else "")}</description_short>
        <description>{escape_xml(description)}</description>
        <price>{price}</price>
        <active>1</active>
        <id_category_default>{prestashop_category_id}</id_category_default>
        <associations>
            <categories>
                <category>
                    <id>{prestashop_category_id}</id>
                </category>
            </categories>
        </associations>
    </product>
</prestashop>"""
            
            response = requests.post(
                f"{self.api_url}/products",
                params={"ws_key": self.api_key, "output_format": "JSON"},
                data=xml_payload.encode('utf-8'),
                headers=self.get_auth_headers(),
                timeout=15,
                verify=False
            )
            
            if response.ok:
                try:
                    response_data = response.json()
                    prestashop_product_id = response_data.get("product", {}).get("id")
                except Exception as parse_err:
                    logger.warning(f"Could not parse response for product '{product.get('product_name')}': {parse_err}")
                    prestashop_product_id = None
                
                if prestashop_product_id:
                    source_product_id = product.get("id")
                    logger.info(f"Created product '{product.get('product_name')}' (source_id: {source_product_id}, prestashop_id: {prestashop_product_id})")
                    self.created_products.append(prestashop_product_id)
                    
                    # Try to add product images
                    self._add_product_images(prestashop_product_id, product)
                    
                    return prestashop_product_id
                else:
                    logger.warning(f"Could not extract product ID from response for '{product.get('product_name')}'")
                    self.failed_operations.append({
                        "type": "product",
                        "data": product,
                        "error": "No ID in response"
                    })
                    return None
            else:
                logger.error(f"Failed to create product '{product.get('product_name')}'. Status: {response.status_code}. Response: {response.text}")
                self.failed_operations.append({
                    "type": "product",
                    "data": product,
                    "status_code": response.status_code,
                    "error": response.text
                })
                return None
                
        except Exception as e:
            logger.error(f"Error while creating product '{product.get('product_name')}': {type(e).__name__}: {e}")
            self.failed_operations.append({
                "type": "product",
                "data": product,
                "error": str(e)
            })
            return None


    def _build_product_description(self, product: Dict) -> str:
        '''
        Builds product description from available fields.

        Parameters:
            product dictionary with product data

        Returns:
            Formatted product description string
        '''
        parts = []
        
        if product.get("description"):
            parts.append(product["description"])
        
        if product.get("display_code"):
            parts.append(f"\nKod produktu: {product['display_code']}")
        
        if product.get("attributes"):
            parts.append("\nAtrybuty:")
            for key, value in product["attributes"].items():
                parts.append(f"  {key}: {value}")
        
        if product.get("tags"):
            parts.append(f"\nTagi: {', '.join(product['tags'])}")
        
        return "\n".join(parts)


    def _add_product_images(self, prestashop_product_id: int, product: Dict) -> bool:
        '''
        Attempts to add product images to Prestashop (optional).

        Parameters:
            prestashop_product_id ID of product in Prestashop
            product               product data with image URLs

        Returns:
            True if successful or no images, False if error occurred
        '''
        try:
            image_url = product.get("thumbnail_high_res") or product.get("thumbnail")
            
            if not image_url:
                return True
            
            # Build XML payload for image
            xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<prestashop>
    <image>
        <id_product>{prestashop_product_id}</id_product>
        <position>1</position>
    </image>
</prestashop>"""
            
            response = requests.post(
                f"{self.api_url}/products/{prestashop_product_id}/images",
                params={"ws_key": self.api_key, "output_format": "JSON"},
                data=xml_payload.encode('utf-8'),
                headers=self.get_auth_headers(),
                timeout=15,
                verify=False
            )
            
            if response.ok:
                logger.debug(f"Added image to product {prestashop_product_id}")
                return True
            else:
                logger.warning(f"Failed to add image to product {prestashop_product_id}. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"Error while adding image to product {prestashop_product_id}: {e}")
            return False


    def create_products(self, limit: Optional[int] = None) -> bool:
        '''
        Creates all products in Prestashop.

        Parameters:
            limit optional maximum number of products to create

        Returns:
            True if all products created successfully, False otherwise
        '''
        if not self.products:
            logger.warning("No products to create. Load products first.")
            return False
        
        logger.info("--- Started creating products ---")
        
        products_to_create = self.products[:limit] if limit else self.products
        total = len(products_to_create)
        created_count = 0
        failed_count = 0
        
        for idx, product in enumerate(products_to_create, 1):
            result = self.create_product(product)
            
            if result:
                created_count += 1
            else:
                failed_count += 1
            
            # Log progress every 100 products
            if idx % 100 == 0:
                logger.info(f"Progress: {idx}/{total} products processed")
        
        logger.info(f"--- Finished creating products. Created: {created_count}, Failed: {failed_count} ---")
        
        return failed_count == 0


    def get_failed_operations(self) -> List[Dict]:
        '''
        Returns list of failed operations.

        Returns:
            List of failed operation details
        '''
        return self.failed_operations


    def get_summary(self) -> Dict[str, Any]:
        '''
        Returns a summary of all operations performed.

        Returns:
            Dictionary with operation statistics
        '''
        return {
            "created_categories": len(self.created_categories),
            "created_products": len(self.created_products),
            "failed_operations": len(self.failed_operations),
            "category_id_mappings": len(self.category_id_map),
            "category_ids": self.created_categories,
            "product_ids": self.created_products,
            "failures": self.failed_operations
        }


    def save_summary(self, path: str = "initialization_summary.json") -> bool:
        '''
        Saves operation summary to a JSON file.

        Parameters:
            path path where to save the summary

        Returns:
            True if saved successfully, False otherwise
        '''
        try:
            summary = self.get_summary()
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=4)
                logger.info(f"Operation summary saved to {path}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save summary: {e}")
            return False
