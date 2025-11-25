import logging
from prestapyt import PrestaShopWebServiceDict
import requests
import subprocess

logger = logging.getLogger(__name__)

class CarrierManager:
    def __init__(self, prestashop_api: PrestaShopWebServiceDict):
        self.prestashop = prestashop_api
        self.carriers_cache = {} # name -> id

    def get_zone_id(self, name="Europe"):
        # Hardcoded for now based on DB check, usually 1
        return 1

    def create_carriers_from_products(self, products):
        logger.info("--- Scanning products for carriers ---")
        
        # Collect unique carriers and their typical costs
        # Map: "Carrier Name" -> cost (float)
        carriers_map = {}
        
        for p in products:
            shipping_info = p.get("shipping_info", {})
            # Map IDs to Names
            id_to_name = {s["id"]: s["name"] for s in shipping_info.get("shippings", [])}
            # Get costs for Poland (179)
            costs = shipping_info.get("country2shipping", {}).get("179", [])
            
            for c in costs:
                ship_id = str(c.get("id"))
                cost_str = str(c.get("lowestCost", "0"))
                try:
                    cost = float(cost_str)
                except ValueError:
                    continue
                
                if cost <= 0: continue # Skip free/pickup for now
                
                name = id_to_name.get(ship_id)
                if name:
                    # Store the cost (overwrite is fine, assume consistent)
                    carriers_map[name] = cost

        logger.info(f"Found {len(carriers_map)} unique carriers to configure: {list(carriers_map.keys())}")
        
        for name, cost in carriers_map.items():
            self.create_carrier(name, cost)
            
        return self.carriers_cache

    def create_carrier(self, name, cost):
        try:
            # 1. Check if exists
            search_opt = {'filter[name]': name, 'limit': 1, 'filter[deleted]': '0'}
            result = self.prestashop.get('carriers', options=search_opt)
            
            carriers_data = result.get('carriers')
            existing = None
            if isinstance(carriers_data, dict):
                existing = carriers_data.get('carrier')
            
            if existing:
                if isinstance(existing, list):
                    c_id = existing[0]['attrs']['id']
                else:
                    c_id = existing['attrs']['id']
                self.carriers_cache[name] = int(c_id)
                return 
            
            # 2. Create Carrier
            # delay: id of delay text (we need to create it or use default?)
            # We need a valid delay text. It's in ps_carrier_lang.
            # We can just pass the text directly in XML if we use the full schema?
            # Prestapyt's 'add' requires a dictionary matching the schema.
            
            carrier_xml = {
                'carrier': {
                    'name': name,
                    'active': '1',
                    'is_free': '0',
                    'url': '',
                    'shipping_handling': '0',
                    'shipping_external': '0',
                    'range_behavior': '0',
                    'shipping_method': '1', # 1 = Billing by Weight
                    'max_width': '0',
                    'max_height': '0',
                    'max_depth': '0',
                    'max_weight': '0',
                    'grade': '0',
                    'delay': {'language': {'attrs': {'id': '1'}, 'value': 'Standard delivery'}},
                }
            }
            
            response = self.prestashop.add('carriers', carrier_xml)
            carrier_id = response['prestashop']['carrier']['id']
            logger.info(f"Created Carrier '{name}' (ID: {carrier_id})")
            
            # 3. Create Range Weight (0 - 10000 kg)
            range_weight_xml = {
                'weight_range': {
                    'id_carrier': carrier_id,
                    'delimiter1': '0.000000',
                    'delimiter2': '10000.000000'
                }
            }
            rw_response = self.prestashop.add('weight_ranges', range_weight_xml)
            range_id = rw_response['prestashop']['weight_range']['id']
            
            # 4. Set Price (Delivery) via SQL to avoid API issues
            # We need: id_carrier, id_range_weight, id_zone, price
            # We use id_range_price = 0
            
            zone_id = self.get_zone_id()
            sql = f"INSERT INTO ps_delivery (id_carrier, id_range_price, id_range_weight, id_zone, price) VALUES ({carrier_id}, 0, {range_id}, {zone_id}, {cost});"
            
            cmd = [
                "docker", "exec", "agrochowski_db",
                "mysql", "-u", "prestashop", "-pprestashop_password", "prestashop",
                "-e", sql
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to insert delivery via SQL: {e.stderr}")
            
            # 5. Associate with Groups (Visitor, Guest, Customer -> 1, 2, 3) via SQL
            # Table: ps_carrier_group (id_carrier, id_group)
            
            group_sql_values = []
            for g_id in [1, 2, 3]:
                group_sql_values.append(f"({carrier_id}, {g_id})")
            
            group_sql = f"INSERT INTO ps_carrier_group (id_carrier, id_group) VALUES {', '.join(group_sql_values)};"
            
            cmd_group = [
                "docker", "exec", "agrochowski_db",
                "mysql", "-u", "prestashop", "-pprestashop_password", "prestashop",
                "-e", group_sql
            ]
            
            try:
                subprocess.run(cmd_group, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to insert carrier groups via SQL: {e.stderr}")
            
            # 6. Associate with Zone (Europe -> 1) via SQL
            # Table: ps_carrier_zone (id_carrier, id_zone)
            
            zone_sql = f"INSERT INTO ps_carrier_zone (id_carrier, id_zone) VALUES ({carrier_id}, {zone_id});"
            
            cmd_zone = [
                "docker", "exec", "agrochowski_db",
                "mysql", "-u", "prestashop", "-pprestashop_password", "prestashop",
                "-e", zone_sql
            ]
            
            try:
                subprocess.run(cmd_zone, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to insert carrier zone via SQL: {e.stderr}")
            
            logger.info(f"Configured Carrier '{name}' with price {cost} zł")
            
            self.carriers_cache[name] = int(carrier_id)
            
        except Exception as e:
            logger.error(f"Failed to create carrier '{name}': {e}")
