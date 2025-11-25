import sys
import os
import json
import logging
import urllib3
import requests
from typing import Dict, List, Optional, Any
from prestapyt import PrestaShopWebServiceDict, PrestaShopWebServiceError
import logging_config
from slugify import slugify

# Disable SSL warnings as we are using self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# TODO: Fix this using proper package structure
# Add parent directory to path to import logging_config from scraper/src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging_config.setup_logging()
logger = logging.getLogger(__name__)


class Initializer:
    """
    Initializer class that collects data about categories and products
    from scraper results and sends them to Prestashop 1.7.8 using REST API webservice.

    This class handles:
    - Loading categories and products from JSON files
    - Authentication with Prestashop API (via prestapyt)
    - Creating categories and products in the Prestashop store
    """

    def __init__(
        self,
        api_url,
        api_key,
        categories_path="scraper/results/categories.json",
        products_path="scraper/results/products.json",
    ):
        """
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

        # Caches to reduce API calls
        self.manufacturers_cache = {}  # name -> id
        self.features_cache = {}  # name -> id
        self.feature_values_cache = {}  # feature_id -> {value -> id}

        # Initialize Prestashop Webservice
        # PrestaShopWebServiceDict does not support verify=False argument directly in older versions,
        try:
            session = requests.Session()
            session.verify = False
            self.prestashop = PrestaShopWebServiceDict(
                self.api_url, self.api_key, session=session
            )
        except Exception as e:
            logger.error(f"Failed to initialize PrestaShopWebServiceDict: {e}")
            raise

    @property
    def api_url(self):
        return self._api_url

    @api_url.setter
    def api_url(self, api_url):
        if not api_url or type(api_url) is not str or not api_url.strip():
            raise ValueError("api_url must be a non-empty string")
        self._api_url = api_url.rstrip("/")

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, api_key):
        if not api_key or type(api_key) is not str or not api_key.strip():
            raise ValueError("api_key must be a non-empty string")
        self._api_key = api_key

    @property
    def categories_path(self):
        return self._categories_path

    @categories_path.setter
    def categories_path(self, categories_path):
        if (
            not categories_path
            or type(categories_path) is not str
            or not categories_path.strip()
        ):
            raise ValueError("categories_path must be a non-empty string")
        self._categories_path = categories_path

    @property
    def products_path(self):
        return self._products_path

    @products_path.setter
    def products_path(self, products_path):
        if (
            not products_path
            or type(products_path) is not str
            or not products_path.strip()
        ):
            raise ValueError("products_path must be a non-empty string")
        self._products_path = products_path

    def test_connection(self) -> bool:
        """
        Tests the connection to Prestashop API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to fetch languages as a lightweight test
            self.prestashop.get("languages", options={"limit": 1})
            logger.info("Successfully connected to Prestashop API")
            return True
        except PrestaShopWebServiceError as e:
            logger.error(f"Failed to connect to Prestashop API: {e}")
            return False
        except Exception as e:
            logger.error(f"Connection error to Prestashop API: {e}")
            return False

    def load_categories(self) -> bool:
        """
        Loads categories from JSON file.

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(self.categories_path, "r", encoding="utf-8") as f:
                self.categories = json.load(f)
                logger.info(
                    f"Loaded {len(self.categories)} top-level categories from {self.categories_path}"
                )
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

    def create_category(self, category: Dict, parent_id: int = 0) -> Optional[int]:
        """
        Creates a single category in Prestashop using prestapyt.

        Parameters:
            category    dictionary with category data
            parent_id   ID of parent category in Prestashop (0 for root)

        Returns:
            New Prestashop category ID if successful, None otherwise
        """
        try:
            # Prepare category data structure for PrestaShop
            # We need to construct the dictionary that matches PrestaShop's schema
            # Using language ID 1 (Polish) as default

            category_schema = {
                "category": {
                    "name": {
                        "language": {
                            "attrs": {"id": "1"},
                            "value": category.get("name"),
                        }
                    },
                    "link_rewrite": {
                        "language": {
                            "attrs": {"id": "1"},
                            "value": slugify(category.get("name", "")),
                        }
                    },
                    "active": "1",
                    "id_parent": str(parent_id),
                    # description can be added here if available
                }
            }

            # Add to PrestaShop
            response = self.prestashop.add("categories", category_schema)

            # Extract ID from response
            # response is usually a dict like {'prestashop': {'category': {'id': '123', ...}}}
            prestashop_id = response.get("prestashop", {}).get("category", {}).get("id")

            if prestashop_id:
                source_id = category.get("id")

                if source_id:
                    self.category_id_map[source_id] = int(prestashop_id)

                logger.info(
                    f"Created category '{category.get('name')}' (source_id: {source_id}, prestashop_id: {prestashop_id})"
                )
                self.created_categories.append(int(prestashop_id))
                return int(prestashop_id)
            else:
                logger.warning(
                    f"No ID in response for category '{category.get('name')}'"
                )
                return None

        except PrestaShopWebServiceError as e:
            logger.error(
                f"PrestaShop API Error creating category '{category.get('name')}': {e}"
            )
            self.failed_operations.append(
                {"type": "category", "data": category, "error": str(e)}
            )
            return None
        except Exception as e:
            logger.error(
                f"Error while creating category '{category.get('name')}': {type(e).__name__}: {e}"
            )
            self.failed_operations.append(
                {"type": "category", "data": category, "error": str(e)}
            )
            return None

    def create_categories(self) -> bool:
        """
        Creates all categories in Prestashop maintaining the hierarchical structure.

        Returns:
            True if all categories created successfully, False otherwise
        """
        if not self.categories:
            logger.warning("No categories to create. Load categories first.")
            return False

        logger.info("--- Started creating categories ---")

        root_categories = self.categories

        def create_categories_recursive(cats: List[Dict], parent_id: int = 0) -> bool:
            """Recursively creates categories maintaining hierarchy"""
            all_success = True

            for cat in cats:
                prestashop_id = self.create_category(cat, parent_id)

                if prestashop_id is None:
                    all_success = False
                    continue

                if cat.get("children"):
                    child_success = create_categories_recursive(
                        cat["children"], prestashop_id
                    )
                    if not child_success:
                        all_success = False

            return all_success

        success = create_categories_recursive(root_categories, 2)

        if success:
            logger.info(
                f"--- Successfully created {len(self.created_categories)} categories ---"
            )
        else:
            logger.warning(
                f"--- Created {len(self.created_categories)} categories with {len(self.failed_operations)} failures ---"
            )

        return success

    def get_or_create_manufacturer(self, name: str) -> Optional[int]:
        """
        Gets existing manufacturer ID or creates a new one.

        Parameters:
            name Name of the manufacturer

        Returns:
            Manufacturer ID or None if failed
        """
        if not name:
            return None

        if name in self.manufacturers_cache:
            return self.manufacturers_cache[name]

        try:
            search_opt = {"filter[name]": name, "limit": 1}
            result = self.prestashop.get("manufacturers", options=search_opt)

            logger.debug(
                f"Search manufacturer '{name}' result type: {type(result)}, content: {result}"
            )

            manufacturers_data = result.get("manufacturers")
            if isinstance(manufacturers_data, dict):
                manufacturers = manufacturers_data.get("manufacturer")
            else:
                manufacturers = None

            if manufacturers:
                if isinstance(manufacturers, list):
                    m_id = int(manufacturers[0]["attrs"]["id"])
                else:
                    m_id = int(manufacturers["attrs"]["id"])
                self.manufacturers_cache[name] = m_id
                return m_id

            # Create new
            manufacturer_schema = {"manufacturer": {"name": name, "active": "1"}}
            response = self.prestashop.add("manufacturers", manufacturer_schema)
            logger.debug(
                f"Add manufacturer response type: {type(response)}, content: {response}"
            )

            if isinstance(response, str):
                logger.error(
                    f"PrestaShop returned string instead of dict for add manufacturer: {response}"
                )
                return None

            m_id = int(response.get("prestashop", {}).get("manufacturer", {}).get("id"))

            self.manufacturers_cache[name] = m_id
            logger.info(f"Created manufacturer: {name} (ID: {m_id})")
            return m_id

        except Exception as e:
            logger.error(f"Error managing manufacturer '{name}': {e}")
            return None

    def get_or_create_feature(self, name: str) -> Optional[int]:
        """
        Gets existing feature ID or creates a new one.
        """
        if not name:
            return None

        if name in self.features_cache:
            return self.features_cache[name]

        try:
            search_opt = {"filter[name]": name, "limit": 1}
            result = self.prestashop.get("product_features", options=search_opt)

            features_data = result.get("product_features")
            if isinstance(features_data, dict):
                features = features_data.get("product_feature")
            else:
                features = None

            if features:
                if isinstance(features, list):
                    f_id = int(features[0]["attrs"]["id"])
                else:
                    f_id = int(features["attrs"]["id"])
                self.features_cache[name] = f_id
                return f_id

            # Create new
            feature_schema = {
                "product_feature": {
                    "name": {"language": {"attrs": {"id": "1"}, "value": name}},
                    "position": "0",
                }
            }
            response = self.prestashop.add("product_features", feature_schema)
            f_id = int(
                response.get("prestashop", {}).get("product_feature", {}).get("id")
            )

            self.features_cache[name] = f_id
            logger.info(f"Created feature: {name} (ID: {f_id})")
            return f_id

        except Exception as e:
            logger.error(f"Error managing feature '{name}': {e}")
            return None

    def get_or_create_feature_value(self, feature_id: int, value: str) -> Optional[int]:
        """
        Gets existing feature value ID or creates a new one.
        """
        if not feature_id or not value:
            return None

        # Check cache
        if feature_id not in self.feature_values_cache:
            self.feature_values_cache[feature_id] = {}

        if value in self.feature_values_cache[feature_id]:
            return self.feature_values_cache[feature_id][value]

        try:
            search_opt = {
                "filter[id_feature]": str(feature_id),
                "filter[value]": value,
                "limit": 1,
            }
            result = self.prestashop.get("product_feature_values", options=search_opt)

            values_data = result.get("product_feature_values")
            if isinstance(values_data, dict):
                values = values_data.get("product_feature_value")
            else:
                values = None

            if values:
                if isinstance(values, list):
                    v_id = int(values[0]["attrs"]["id"])
                else:
                    v_id = int(values["attrs"]["id"])
                self.feature_values_cache[feature_id][value] = v_id
                return v_id

            # Create new
            value_schema = {
                "product_feature_value": {
                    "id_feature": str(feature_id),
                    "value": {"language": {"attrs": {"id": "1"}, "value": value}},
                    "custom": "0",
                }
            }
            response = self.prestashop.add("product_feature_values", value_schema)
            v_id = int(
                response.get("prestashop", {})
                .get("product_feature_value", {})
                .get("id")
            )

            self.feature_values_cache[feature_id][value] = v_id
            return v_id

        except Exception as e:
            logger.error(
                f"Error managing feature value '{value}' for feature {feature_id}: {e}"
            )
            return None

    def create_product(self, product: Dict) -> Optional[int]:
        """
        Creates a single product in Prestashop using requests directly to handle 500 responses.

        Parameters:
            product dictionary with product data from scraper

        Returns:
            New Prestashop product ID if successful, None otherwise
        """
        try:
            source_category_id = product.get("category_id")
            prestashop_category_id = self.category_id_map.get(source_category_id)

            if not prestashop_category_id:
                logger.warning(
                    f"No category mapping found for product '{product.get('product_name')}'. Skipping..."
                )
                self.failed_operations.append(
                    {
                        "type": "product",
                        "data": product,
                        "error": "Category mapping not found",
                    }
                )
                return None

            price_str = (
                product.get("price", {})
                .get("current", "0")
                .replace(" zł", "")
                .replace(",", ".")
                .replace("\u00a0", "")
            )
            try:
                price = float(price_str) if price_str else 0.0
            except ValueError:
                price = 0.0

            # Reference / SKU
            reference = product.get("display_code", "")

            # Manufacturer (Publisher)
            manufacturer_id = ""
            attributes = product.get("attributes", {})
            publisher_name = attributes.get("wydawnictwo") or attributes.get(
                "Wydawnictwo"
            )
            if publisher_name:
                m_id = self.get_or_create_manufacturer(publisher_name)
                if m_id:
                    manufacturer_id = str(m_id)

            # Features
            product_features_xml = ""

            # 1. Author as Feature
            author = product.get("product_author")
            if author:
                f_id = self.get_or_create_feature("Autor")
                if f_id:
                    v_id = self.get_or_create_feature_value(f_id, author)
                    if v_id:
                        product_features_xml += f"<product_feature><id>{f_id}</id><id_feature_value>{v_id}</id_feature_value></product_feature>"

            # 2. Attributes as Features
            for key, value in attributes.items():
                if key.lower() in ["wydawnictwo", "waga"]:
                    continue

                feature_name = key.replace("_", " ").capitalize()

                f_id = self.get_or_create_feature(feature_name)
                if f_id:
                    v_id = self.get_or_create_feature_value(f_id, str(value))
                    if v_id:
                        product_features_xml += f"<product_feature><id>{f_id}</id><id_feature_value>{v_id}</id_feature_value></product_feature>"

            description = self._build_product_description(product)

            # XML construction
            # Escape XML special characters
            def escape_xml(text):
                if not text:
                    return ""
                return (
                    str(text)
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                    .replace("'", "&apos;")
                )

            xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
<prestashop>
    <product>
        <name>
            <language id="1">{escape_xml(product.get("product_name", "Unknown"))}</language>
        </name>
        <link_rewrite>
            <language id="1">{escape_xml(slugify(product.get("product_name", "Unknown")))}</language>
        </link_rewrite>
        <description>
            <language id="1">{escape_xml(description)}</language>
        </description>
        <description_short>
            <language id="1">{escape_xml(description[:200] if description else "")}</language>
        </description_short>
        <price>{price}</price>
        <id_tax_rules_group>1</id_tax_rules_group>
        <minimal_quantity>1</minimal_quantity>
        <available_for_order>1</available_for_order>
        <show_price>1</show_price>
        <id_shop_default>1</id_shop_default>
        <indexed>1</indexed>
        <reference>{escape_xml(reference)}</reference>
        <active>1</active>
        <state>1</state>
        <id_category_default>{prestashop_category_id}</id_category_default>
        <id_manufacturer>{manufacturer_id}</id_manufacturer>
        <associations>
            <categories>
                <category>
                    <id>{prestashop_category_id}</id>
                </category>
            </categories>
            <product_features>
                {product_features_xml}
            </product_features>
        </associations>
    </product>
</prestashop>"""

            url = f"{self.api_url}/products"

            params = {"ws_key": self.api_key, "output_format": "JSON"}
            headers = {"Content-Type": "application/xml"}

            response = self.prestashop.client.post(
                url, params=params, data=xml_payload.encode("utf-8"), headers=headers
            )

            if response.status_code in [200, 201] or response.text:
                try:
                    response_data = response.json()
                    # It might be nested in 'product' or 'products'
                    product_node = response_data.get("product")
                    if product_node:
                        prestashop_product_id = product_node.get("id")
                        if prestashop_product_id:
                            source_product_id = product.get("id")
                            logger.info(
                                f"Created product '{product.get('product_name')}' (source_id: {source_product_id}, prestashop_id: {prestashop_product_id})"
                            )
                            self.created_products.append(int(prestashop_product_id))

                            self._add_product_images(
                                int(prestashop_product_id), product
                            )
                            return int(prestashop_product_id)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse response JSON for product '{product.get('product_name')}': {e}"
                    )
                    pass

            if response.status_code not in [200, 201]:
                logger.warning(
                    f"Failed to create product '{product.get('product_name')}' (Status: {response.status_code}). Response: {response.text[:200]}"
                )

            return None

        except Exception as e:
            logger.error(
                f"Error while creating product '{product.get('product_name')}': {type(e).__name__}: {e}"
            )
            self.failed_operations.append(
                {"type": "product", "data": product, "error": str(e)}
            )
            return None

    def _build_product_description(self, product: Dict) -> str:
        """
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


    def remove_all_products(self) -> bool:
        '''
        Removes all products from PrestaShop.

        Returns:
            True if successful, False otherwise
        '''
        try:
            logger.info("--- Started removing all products ---")
            
            # Get all products (without display=full to avoid PHP notices)
            response = requests.get(
                f"{self.api_url}/products",
                params={"ws_key": self.api_key, "output_format": "JSON"},
                headers=self.get_auth_headers(),
                timeout=15,
                verify=False
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch products list. Status: {response.status_code}")
                return False
            
            products_data = response.json()
            
            # Handle different response formats
            if isinstance(products_data, dict):
                products = products_data.get("products", [])
            else:
                products = products_data if isinstance(products_data, list) else []
            
            # Ensure products is a list of dicts, not a list of primitive types
            if not products or not isinstance(products, list):
                logger.info("No products to remove")
                return True
            
            # Filter out non-dict entries (some API responses may have mixed types)
            products = [p for p in products if isinstance(p, dict)]
            
            if not products:
                logger.info("No products to remove")
                return True
            
            logger.info(f"Found {len(products)} products to remove")
            
            removed_count = 0
            failed_count = 0
            
            for product in products:
                if not isinstance(product, dict):
                    logger.warning(f"Skipping invalid product entry: {product}")
                    continue
                
                product_id = product.get("id")
                product_name = product.get("name", "Unknown")
                
                try:
                    delete_response = requests.delete(
                        f"{self.api_url}/products/{product_id}",
                        params={"ws_key": self.api_key},
                        headers=self.get_auth_headers(),
                        timeout=10,
                        verify=False
                    )
                    
                    # Accept 200, 204, or 500 with valid response (PHP notices)
                    if delete_response.status_code in [200, 204]:
                        logger.info(f"Removed product {product_id}: {product_name}")
                        removed_count += 1
                    elif delete_response.status_code == 500:
                        # Check if deletion was successful despite HTTP 500
                        try:
                            response_body = delete_response.json()
                            # If no errors or only PHP notices, consider it a success
                            if "errors" not in response_body or not response_body.get("errors"):
                                logger.info(f"Removed product {product_id}: {product_name}")
                                removed_count += 1
                            else:
                                logger.warning(f"Failed to remove product {product_id} ({product_name}). Errors: {response_body.get('errors')}")
                                failed_count += 1
                        except:
                            logger.warning(f"Failed to remove product {product_id} ({product_name}). Status: 500")
                            failed_count += 1
                    else:
                        logger.warning(f"Failed to remove product {product_id} ({product_name}). Status: {delete_response.status_code}")
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error removing product {product_id}: {e}")
                    failed_count += 1
            
            logger.info(f"--- Finished removing products. Removed: {removed_count}, Failed: {failed_count} ---")
            return failed_count == 0
            
        except Exception as e:
            logger.error(f"Error while removing products: {type(e).__name__}: {e}")
            return False


    
    def remove_all_categories(self) -> bool:
        '''
        Removes all non-basic categories from PrestaShop.
        Only keeps the root category (id=1) and its direct children (Baza/Root).

        Returns:
            True if successful, False otherwise
        '''
        try:
            logger.info("--- Started removing all non-basic categories ---")
            
            # Get all categories with full details
            response = requests.get(
                f"{self.api_url}/categories",
                params={"ws_key": self.api_key, "output_format": "JSON", "display": "full"},
                headers=self.get_auth_headers(),
                timeout=15,
                verify=False
            )
            
            # Accept 200 or 500 (PrestaShop returns 500 with valid JSON due to PHP notices)
            if response.status_code not in [200, 500]:
                logger.error(f"Failed to fetch categories list. Status: {response.status_code}")
                return False
            
            try:
                categories_data = response.json()
            except:
                logger.error("Failed to parse categories response as JSON")
                return False
            
            categories = categories_data.get("categories", [])
            
            if not categories:
                logger.info("No categories to remove")
                return True
            
            logger.info(f"Found {len(categories)} categories to evaluate")
            
            # Sort by level_depth descending to remove leaf categories first
            categories_sorted = sorted(categories, key=lambda x: int(x.get("level_depth", 0)), reverse=True)
            
            removed_count = 0
            failed_count = 0
            skipped_count = 0
            
            for category in categories_sorted:
                category_id = category.get("id")
                category_name = category.get("name", [{}])[0].get("value", "Unknown") if isinstance(category.get("name"), list) else category.get("name", "Unknown")
                level_depth = int(category.get("level_depth", 0))
                
                # Skip root category (id=1) ONLY - compare as strings and ints
                if str(category_id) == "1" or category_id == 1:
                    logger.info(f"Skipping root category (id=1)")
                    skipped_count += 1
                    continue
                
                # Remove ALL other categories (including those with level_depth=0)
                try:
                    delete_response = requests.delete(
                        f"{self.api_url}/categories/{category_id}",
                        params={"ws_key": self.api_key},
                        headers=self.get_auth_headers(),
                        timeout=10,
                        verify=False
                    )
                    
                    # Accept 200, 204, or 500 with valid response (PHP notices)
                    if delete_response.status_code in [200, 204]:
                        logger.info(f"Removed category {category_id}: {category_name} (level_depth={level_depth})")
                        removed_count += 1
                    elif delete_response.status_code == 500:
                        # Check if deletion was successful despite HTTP 500
                        try:
                            response_body = delete_response.json()
                            # If no errors or only PHP notices, consider it a success
                            if "errors" not in response_body or not response_body.get("errors"):
                                logger.info(f"Removed category {category_id}: {category_name} (level_depth={level_depth})")
                                removed_count += 1
                            else:
                                logger.warning(f"Failed to remove category {category_id} ({category_name}). Errors: {response_body.get('errors')}")
                                failed_count += 1
                        except:
                            logger.warning(f"Failed to remove category {category_id} ({category_name}). Status: 500")
                            failed_count += 1
                    else:
                        logger.warning(f"Failed to remove category {category_id} ({category_name}). Status: {delete_response.status_code}")
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error removing category {category_id}: {e}")
                    failed_count += 1
            
            logger.info(f"--- Finished removing categories. Removed: {removed_count}, Skipped: {skipped_count}, Failed: {failed_count} ---")
            return failed_count == 0
            
        except Exception as e:
            logger.error(f"Error while removing all categories: {type(e).__name__}: {e}")
            return False
