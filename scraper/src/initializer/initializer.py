import re
import sys
import os
import json
import logging
import urllib3
import requests
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from typing import Dict, List, Optional, Any
from prestapyt import PrestaShopWebServiceDict, PrestaShopWebServiceError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging_config
from slugify import slugify

# Disable SSL warnings as we might be using self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add parent directory to path to import logging_config from scraper/src

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
        """

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

        # Thread safety locks
        self.lock = threading.Lock()
        self.cache_lock = threading.Lock()

        # Initialize Prestashop Webservice
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
        """
        Loads products from JSON file.

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(self.products_path, "r", encoding="utf-8") as f:
                self.products = json.load(f)
                logger.info(
                    f"Loaded {len(self.products)} products from {self.products_path}"
                )
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
                }
            }

            # Add to PrestaShop
            response = self.prestashop.add("categories", category_schema)

            # Extract ID from response
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
        Gets existing manufacturer ID or creates a new one. Thread-safe.
        """
        if not name:
            return None

        with self.cache_lock:
            if name in self.manufacturers_cache:
                return self.manufacturers_cache[name]

            try:
                # Search for existing
                search_opt = {"filter[name]": name, "limit": 1}
                result = self.prestashop.get("manufacturers", options=search_opt)

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

                if isinstance(response, str):
                    logger.error(
                        f"PrestaShop returned string instead of dict for add manufacturer: {response}"
                    )
                    return None

                m_id = int(
                    response.get("prestashop", {}).get("manufacturer", {}).get("id")
                )

                self.manufacturers_cache[name] = m_id
                logger.info(f"Created manufacturer: {name} (ID: {m_id})")
                return m_id

            except Exception as e:
                logger.error(f"Error managing manufacturer '{name}': {e}")
                return None

    def get_or_create_feature(self, name: str) -> Optional[int]:
        """
        Gets existing feature ID or creates a new one. Thread-safe.
        """
        if not name:
            return None

        with self.cache_lock:
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
        Gets existing feature value ID or creates a new one. Thread-safe.
        """
        if not feature_id or not value:
            return None

        with self.cache_lock:
            # Check cache
            if feature_id not in self.feature_values_cache:
                self.feature_values_cache[feature_id] = {}

            if value in self.feature_values_cache[feature_id]:
                return self.feature_values_cache[feature_id][value]

            try:
                # Search for existing value for this feature
                search_opt = {
                    "filter[id_feature]": str(feature_id),
                    "filter[value]": value,
                    "limit": 1,
                }
                result = self.prestashop.get(
                    "product_feature_values", options=search_opt
                )

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

    def update_stock_available(self, product_id: int, quantity: int = 1) -> bool:
        """
        Updates the stock quantity for a product.

        Parameters:
            product_id  ID of the product in PrestaShop
            quantity    New quantity to set (default 1)

        Returns:
            True if successful, False otherwise
        """
        try:
            # First, find the stock_available ID for this product
            search_opt = {"filter[id_product]": product_id, "limit": 1}
            result = self.prestashop.get("stock_availables", options=search_opt)

            stock_data = result.get("stock_availables")
            if isinstance(stock_data, dict):
                stock_item = stock_data.get("stock_available")
            else:
                stock_item = None

            if stock_item:
                if isinstance(stock_item, list):
                    stock_id = int(stock_item[0]["attrs"]["id"])
                else:
                    stock_id = int(stock_item["attrs"]["id"])

                # Now get the full XML for this stock item to update it
                stock_xml = self.prestashop.get(
                    "stock_availables", resource_id=stock_id
                )

                # Update quantity
                stock_xml["stock_available"]["quantity"] = quantity

                # Send update
                self.prestashop.edit("stock_availables", stock_xml)
                # logger.info(f"Updated stock for product {product_id} to {quantity}")
                return True
            else:
                logger.warning(
                    f"No stock_available record found for product {product_id}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to update stock for product {product_id}: {e}")
            return False

    def create_product(self, product: Dict) -> Optional[int]:
        """
        Creates a single product in Prestashop using requests directly to handle 500 responses.
        Designed to be run in a thread.

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
                with self.lock:
                    self.failed_operations.append(
                        {
                            "type": "product",
                            "data": product,
                            "error": "Category mapping not found",
                        }
                    )
                return None

            # Fix Price Parsing
            raw_price = product.get("price", {}).get("current", "0")
            # Replace comma with dot for float parsing
            normalized_price = raw_price.replace(",", ".").replace(" ", "")
            # Extract number using regex (supports 36.00, 36.00zł, etc)
            match = re.search(r"(\d+(\.\d+)?)", normalized_price)

            if match:
                try:
                    price = float(match.group(1))
                except ValueError:
                    price = 0.0
            else:
                price = 0.0

            if price == 0.0:
                logger.warning(
                    f"Price is 0.0 for product {product.get('product_name')} (Raw: '{raw_price}')"
                )

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

            # Helper to add feature
            def add_feature(name, val):
                if not val:
                    return ""
                f_id_local = self.get_or_create_feature(name)
                if f_id_local:
                    v_id_local = self.get_or_create_feature_value(f_id_local, str(val))
                    if v_id_local:
                        return f"<product_feature><id>{f_id_local}</id><id_feature_value>{v_id_local}</id_feature_value></product_feature>"
                return ""

            # 1. Author as Feature
            author = product.get("product_author")
            product_features_xml += add_feature("Autor", author)

            # 2. Specific requested features
            # "Tłumacz", "Kod produktu", "Liczba stron", "Rok wydania", "Wydawnictwo", "Wysokość", "Oprawa", "Stan książki"

            # Explicitly add specific attributes even if they duplicate standard fields
            product_features_xml += add_feature("Wydawnictwo", publisher_name)
            product_features_xml += add_feature("Kod produktu", reference)

            # Add other attributes
            for key, value in attributes.items():
                if key.lower() == "wydawnictwo":
                    continue  # Already added above explicitly

                # Normalize key to display name
                feature_name_map = {
                    "liczba_stron": "Liczba stron",
                    "rok_wydania": "Rok wydania",
                    "wysokość": "Wysokość",
                    "oprawa": "Oprawa",
                    "stan_książki": "Stan książki",
                    "tłumacz": "Tłumacz",
                }

                display_name = feature_name_map.get(
                    key.lower(), key.replace("_", " ").capitalize()
                )
                product_features_xml += add_feature(display_name, value)

            description = self._build_product_description(product)

            # "Nowość" (New) Tag Logic
            # PrestaShop considers a product "New" based on date_add.
            # If tag "Nowość" exists -> use current time.
            # If not -> use older time (e.g. 30 days ago) to prevent "New" label.
            tags = product.get("tags", [])
            is_new = "Nowość" in tags or "nowość" in tags

            now = datetime.now()
            if is_new:
                date_add = now.strftime("%Y-%m-%d %H:%M:%S")
            else:
                # Set to 30 days ago
                date_add = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

            # Dimensions and Weight
            # Default PrestaShop unit is usually cm and kg
            # Source data "Wysokość": "180" -> likely mm. "Waga": "0.5" -> likely kg?

            width = 0.0
            height = 0.0
            depth = 0.0
            weight = 0.0

            # Helper to parse float
            def parse_float(val):
                if not val:
                    return 0.0
                try:
                    return float(
                        str(val)
                        .replace(",", ".")
                        .replace(" ", "")
                        .replace("mm", "")
                        .replace("cm", "")
                        .replace("kg", "")
                        .replace("g", "")
                    )
                except ValueError:
                    return 0.0

            # Map attributes
            condition = "new"  # Default
            isbn = ""

            for key, val in attributes.items():
                k = key.lower()
                v = parse_float(val)

                if "wysoko" in k or "height" in k:
                    if v > 50:
                        height = v / 10.0
                    else:
                        height = v
                elif "szeroko" in k or "width" in k:
                    if v > 50:
                        width = v / 10.0
                    else:
                        width = v
                elif "głęboko" in k or "depth" in k or "grubo" in k:
                    if v > 50:
                        depth = v / 10.0
                    else:
                        depth = v
                elif "waga" in k or "weight" in k:
                    if v > 1000:
                        weight = v / 1000.0
                    else:
                        weight = v
                elif "stan" in k and "ksi" in k:  # stan_książki
                    # If value implies used (digits 1-5 or words), set used
                    # If contains "now" -> new
                    val_lower = str(val).lower()
                    if "now" in val_lower:
                        condition = "new"
                    else:
                        condition = "used"
                elif "isbn" in k:
                    isbn = str(val).replace("-", "").strip()

                # Default weight if missing (books usually ~0.3-0.5kg)
            if weight == 0.0:
                weight = 0.5

            # Shipping Logic
            shipping_info = product.get("shipping_info", {})
            shippings_meta = {s["id"]: s for s in shipping_info.get("shippings", [])}
            poland_costs = shipping_info.get("country2shipping", {}).get("179", [])

            additional_shipping_cost = 0.0

            # Calculate cheapest non-zero shipping for the "Additional Cost" field
            if poland_costs:
                costs = []
                for c in poland_costs:
                    try:
                        cost = float(c.get("lowestCost", 0.0))
                        # We usually want the cheapest *delivery*, not pickup (0.0)
                        # unless pickup is the only option.
                        if cost > 0.01:
                            costs.append(cost)
                    except ValueError:
                        pass

                if costs:
                    additional_shipping_cost = min(costs)

            # XML construction
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
        <width>{width}</width>
        <height>{height}</height>
        <depth>{depth}</depth>
        <weight>{weight}</weight>
        <additional_shipping_cost>{additional_shipping_cost}</additional_shipping_cost>
        <id_shop_default>1</id_shop_default>
        <indexed>1</indexed>
        <reference>{escape_xml(reference)}</reference>
        <isbn>{isbn}</isbn>
        <condition>{condition}</condition>
        <show_condition>1</show_condition>
        <active>1</active>
        <state>1</state>
        <date_add>{date_add}</date_add>
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

            # Using the shared session (self.prestashop.client)
            # requests.Session is thread-safe
            response = self.prestashop.client.post(
                url, params=params, data=xml_payload.encode("utf-8"), headers=headers
            )

            prestashop_product_id = None

            if response.status_code in [200, 201] or response.text:
                try:
                    response_data = response.json()
                    product_node = response_data.get("product")
                    if product_node:
                        prestashop_product_id = product_node.get("id")
                except Exception:
                    pass

            if prestashop_product_id:
                source_product_id = product.get("id")
                logger.info(
                    f"Created product '{product.get('product_name')}' (source_id: {source_product_id}, prestashop_id: {prestashop_product_id})"
                )

                with self.lock:
                    self.created_products.append(int(prestashop_product_id))

                self._add_product_images(int(prestashop_product_id), product)

                # Update Stock Quantity to 1
                self.update_stock_available(int(prestashop_product_id), 1)

                return int(prestashop_product_id)
            else:
                logger.warning(
                    f"Failed to create product '{product.get('product_name')}' (Status: {response.status_code}). Response: {response.text[:200]}"
                )
                with self.lock:
                    self.failed_operations.append(
                        {
                            "type": "product",
                            "data": product,
                            "error": f"API Error: {response.status_code}",
                        }
                    )
                return None

        except Exception as e:
            logger.error(
                f"Error while creating product '{product.get('product_name')}': {type(e).__name__}: {e}"
            )
            with self.lock:
                self.failed_operations.append(
                    {"type": "product", "data": product, "error": str(e)}
                )
            return None

    def _build_product_description(self, product: Dict) -> str:
        """
        Builds product description from available fields.
        """
        parts = []

        if product.get("description"):
            parts.append(product["description"])

        if product.get("display_code"):
            parts.append(
                f"<p><strong>Kod produktu:</strong> {product['display_code']}</p>"
            )

        # Shipping Info
        shipping_info = product.get("shipping_info", {})
        shippings = shipping_info.get("shippings", [])
        if shippings:
            parts.append("<h3>Wysyłka</h3>")
            parts.append("<ul>")
            for ship in shippings:
                name = ship.get("name", "")
                price_gross = ship.get("cost_gross", "")
                parts.append(f"<li>{name}: {price_gross}</li>")
            parts.append("</ul>")

        return "\n".join(parts)

    def _add_product_images(self, prestashop_product_id: int, product: Dict) -> bool:
        """
        Attempts to add product images to Prestashop.
        """
        try:
            image_url = product.get("thumbnail_high_res") or product.get("thumbnail")

            if not image_url:
                return True

            if image_url.startswith("/"):
                image_url = "https://agrochowski.pl" + image_url

            # Download image (thread-safe, new request)
            img_response = requests.get(image_url, verify=False, timeout=15)

            if img_response.status_code == 200:
                # Parse URL to get clean filename without query parameters
                parsed_url = urlparse(image_url)
                filename = os.path.basename(parsed_url.path) or "image.jpg"

                # Use requests to upload image
                url = f"{self.api_url}/images/products/{prestashop_product_id}"
                params = {"ws_key": self.api_key}

                # Determine mime type (simple guess)
                mime_type = "image/jpeg"
                if filename.lower().endswith(".png"):
                    mime_type = "image/png"
                elif filename.lower().endswith(".gif"):
                    mime_type = "image/gif"

                files = {"image": (filename, img_response.content, mime_type)}

                r = requests.post(url, params=params, files=files, verify=False)

                if r.status_code in [200, 201]:
                    logger.info(f"Added image to product {prestashop_product_id}")
                    return True
                else:
                    logger.warning(
                        f"Failed to upload image to product {prestashop_product_id}. Status: {r.status_code}, Response: {r.text}"
                    )
                    return False
            else:
                logger.warning(f"Failed to download image from {image_url}")
                return False

        except Exception as e:
            logger.warning(
                f"Error while adding image to product {prestashop_product_id}: {e}"
            )
            return False

    def create_products(
        self,
        limit: Optional[int] = None,
        max_workers: int = 8,
    ) -> bool:
        """
        Creates products in Prestashop using multithreading.

        Parameters:
            limit       optional maximum number of products to create
            max_workers number of concurrent threads (default 8)

        Returns:
            True if all attempted products created successfully
        """
        if not self.products:
            logger.warning("No products to create. Load products first.")
            return False

        products_to_create = self.products[:limit] if limit else self.products
        total = len(products_to_create)

        logger.info(
            f"--- Started creating {total} products with {max_workers} workers ---"
        )

        created_count = 0
        failed_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Map future to product for tracking
            future_to_product = {
                executor.submit(self.create_product, p): p for p in products_to_create
            }

            completed = 0
            for future in as_completed(future_to_product):
                completed += 1
                try:
                    result = future.result()
                    if result:
                        created_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Thread generated an exception: {e}")

                if completed % 50 == 0:
                    logger.info(f"Progress: {completed}/{total} products processed")

        logger.info(
            f"--- Finished creating products. Created: {created_count}, Failed: {failed_count} ---"
        )

        return failed_count == 0

    def get_failed_operations(self) -> List[Dict]:
        """
        Returns list of failed operations.
        """
        return self.failed_operations

    def get_summary(self) -> Dict[str, Any]:
        """
        Returns a summary of all operations performed.
        """
        return {
            "created_categories": len(self.created_categories),
            "created_products": len(self.created_products),
            "failed_operations": len(self.failed_operations),
            "category_id_mappings": len(self.category_id_map),
            "category_ids": self.created_categories,
            "product_ids": self.created_products,
            "failures": self.failed_operations,
        }

    def save_summary(self, path: str = "initialization_summary.json") -> bool:
        """
        Saves operation summary to a JSON file.
        """
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
        """
        Removes all products from PrestaShop using prestapyt.
        """
        try:
            logger.info("--- Started removing all products ---")

            try:
                products_wrapper = self.prestashop.get("products")
            except PrestaShopWebServiceError as e:
                logger.info(f"Failed to get products (maybe none exist): {e}")
                return True

            products = products_wrapper.get("products", {}).get("product", [])

            if isinstance(products, dict):
                products = [products]

            if not products:
                logger.info("No products to remove")
                return True

            logger.info(f"Found {len(products)} products to remove")

            removed_count = 0
            failed_count = 0

            # Parallel deletion could also be done, but let's keep it simple for now
            # as removal is usually one-off.

            for product_ref in products:
                product_id = product_ref["attrs"]["id"]
                try:
                    self.prestashop.delete("products", resource_ids=product_id)
                    logger.info(f"Removed product {product_id}")
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove product {product_id}: {e}")
                    failed_count += 1

            logger.info(
                f"--- Finished removing products. Removed: {removed_count}, Failed: {failed_count} ---"
            )
            return failed_count == 0

        except Exception as e:
            logger.error(f"Error while removing products: {type(e).__name__}: {e}")
            return False

    def remove_all_categories(self) -> bool:
        """
        Removes all non-basic categories from PrestaShop.
        Only keeps the root category (id=1) and Home (id=2).
        """
        try:
            logger.info("--- Started removing all non-basic categories ---")

            try:
                categories_wrapper = self.prestashop.get("categories")
            except PrestaShopWebServiceError as e:
                logger.info(f"Failed to get categories: {e}")
                return True

            categories = categories_wrapper.get("categories", {}).get("category", [])

            if isinstance(categories, dict):
                categories = [categories]

            if not categories:
                logger.info("No categories to remove")
                return True

            try:
                categories_full = self.prestashop.get(
                    "categories", options={"display": "full"}
                )
                categories_list = categories_full.get("categories", {}).get(
                    "category", []
                )
                if isinstance(categories_list, dict):
                    categories_list = [categories_list]
            except Exception as e:
                logger.error(f"Failed to fetch full categories details: {e}")
                return False

            logger.info(f"Found {len(categories_list)} categories to evaluate")

            # Sort by level_depth descending
            categories_sorted = sorted(
                categories_list,
                key=lambda x: int(x.get("level_depth", 0)),
                reverse=True,
            )

            removed_count = 0
            failed_count = 0
            skipped_count = 0

            for category in categories_sorted:
                category_id = category.get("id")
                level_depth = int(category.get("level_depth", 0))

                # Keep Root (1) and Home (2)
                if str(category_id) in ["1", "2"]:
                    skipped_count += 1
                    continue

                try:
                    self.prestashop.delete("categories", resource_ids=category_id)
                    logger.info(
                        f"Removed category {category_id} (level_depth={level_depth})"
                    )
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove category {category_id}: {e}")
                    failed_count += 1

            logger.info(
                f"--- Finished removing categories. Removed: {removed_count}, Skipped: {skipped_count}, Failed: {failed_count} ---"
            )
            return failed_count == 0

        except Exception as e:
            logger.error(
                f"Error while removing all categories: {type(e).__name__}: {e}"
            )
            return False
