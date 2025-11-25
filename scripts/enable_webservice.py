import subprocess
import secrets
import string
import sys

# Configuration
DB_USER = "root"
DB_PASS = "admin_password"
DB_NAME = "prestashop"
CONTAINER = "agrochowski_db"
DEFAULT_API_KEY = "e44a97fbf306a8059ab8d633a7e55e49"

def generate_api_key():
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))

def enable_webservice(api_key=None):
    if not api_key:
        api_key = DEFAULT_API_KEY
    
    print(f"Enabling Webservice and creating API Key: {api_key}")

    # SQL to enable webservice and add key
    # We use INSERT ON DUPLICATE KEY UPDATE to ensure PS_WEBSERVICE entry exists
    sql_commands = f"""
INSERT INTO ps_configuration (id_shop_group, id_shop, name, value, date_add, date_upd) 
VALUES (NULL, NULL, 'PS_WEBSERVICE', '1', NOW(), NOW()) 
ON DUPLICATE KEY UPDATE value = '1', date_upd = NOW();

DELETE FROM ps_webservice_account WHERE `key` = '{api_key}';
INSERT INTO ps_webservice_account (`key`, description, class_name, is_module, active) VALUES ('{api_key}', 'Initializer Key', '', 0, 1);

SET @id_account = (SELECT id_webservice_account FROM ps_webservice_account WHERE `key` = '{api_key}');

DELETE FROM ps_webservice_account_shop WHERE id_webservice_account = @id_account;
INSERT INTO ps_webservice_account_shop (id_webservice_account, id_shop) VALUES (@id_account, 1);

DELETE FROM ps_webservice_permission WHERE id_webservice_account = @id_account;

-- Grant permissions for needed resources
INSERT INTO ps_webservice_permission (resource, method, id_webservice_account)
SELECT 'categories', 'GET', @id_account UNION ALL
SELECT 'categories', 'POST', @id_account UNION ALL
SELECT 'categories', 'PUT', @id_account UNION ALL
SELECT 'categories', 'DELETE', @id_account UNION ALL
SELECT 'products', 'GET', @id_account UNION ALL
SELECT 'products', 'POST', @id_account UNION ALL
SELECT 'products', 'PUT', @id_account UNION ALL
SELECT 'products', 'DELETE', @id_account UNION ALL
SELECT 'images', 'GET', @id_account UNION ALL
SELECT 'images', 'POST', @id_account UNION ALL
SELECT 'images', 'PUT', @id_account UNION ALL
SELECT 'images', 'DELETE', @id_account UNION ALL
SELECT 'stock_availables', 'GET', @id_account UNION ALL
SELECT 'stock_availables', 'POST', @id_account UNION ALL
SELECT 'stock_availables', 'PUT', @id_account UNION ALL
SELECT 'stock_availables', 'DELETE', @id_account UNION ALL
SELECT 'manufacturers', 'GET', @id_account UNION ALL
SELECT 'manufacturers', 'POST', @id_account UNION ALL
SELECT 'manufacturers', 'PUT', @id_account UNION ALL
SELECT 'manufacturers', 'DELETE', @id_account UNION ALL
SELECT 'product_features', 'GET', @id_account UNION ALL
SELECT 'product_features', 'POST', @id_account UNION ALL
SELECT 'product_features', 'PUT', @id_account UNION ALL
SELECT 'product_features', 'DELETE', @id_account UNION ALL
SELECT 'product_feature_values', 'GET', @id_account UNION ALL
SELECT 'product_feature_values', 'POST', @id_account UNION ALL
SELECT 'product_feature_values', 'PUT', @id_account UNION ALL
SELECT 'product_feature_values', 'DELETE', @id_account UNION ALL
SELECT 'languages', 'GET', @id_account UNION ALL
SELECT 'tax_rule_groups', 'GET', @id_account UNION ALL
SELECT 'shops', 'GET', @id_account UNION ALL
SELECT 'carriers', 'GET', @id_account UNION ALL
SELECT 'carriers', 'POST', @id_account UNION ALL
SELECT 'carriers', 'PUT', @id_account UNION ALL
SELECT 'carriers', 'DELETE', @id_account UNION ALL
SELECT 'weight_ranges', 'GET', @id_account UNION ALL
SELECT 'weight_ranges', 'POST', @id_account UNION ALL
SELECT 'weight_ranges', 'PUT', @id_account UNION ALL
SELECT 'weight_ranges', 'DELETE', @id_account UNION ALL
SELECT 'price_ranges', 'GET', @id_account UNION ALL
SELECT 'price_ranges', 'POST', @id_account UNION ALL
SELECT 'price_ranges', 'PUT', @id_account UNION ALL
SELECT 'price_ranges', 'DELETE', @id_account UNION ALL
SELECT 'deliveries', 'GET', @id_account UNION ALL
SELECT 'deliveries', 'POST', @id_account UNION ALL
SELECT 'deliveries', 'PUT', @id_account UNION ALL
SELECT 'deliveries', 'DELETE', @id_account;
"""

    # Build the docker exec command
    # We use subprocess.run with input=sql_commands to pipe the SQL to mysql
    cmd = [
        "docker", "exec", "-i", CONTAINER,
        "mysql", f"-u{DB_USER}", f"-p{DB_PASS}", DB_NAME
    ]

    try:
        result = subprocess.run(
            cmd,
            input=sql_commands,
            text=True, # This handles string encoding for input/output
            capture_output=True
        )

        if result.returncode == 0:
            print("Successfully enabled Webservice and added API Key.")
            print(f"API Key: {api_key}")
            return True
        else:
            print("Failed to execute SQL.")
            print("Error output:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("Error: 'docker' command not found. Please ensure Docker is installed and in your PATH.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    # If run directly, use the default key or one provided as arg
    key = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_API_KEY
    enable_webservice(key)
