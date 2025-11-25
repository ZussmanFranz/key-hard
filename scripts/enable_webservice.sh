#!/bin/bash

# Configuration
DB_USER="root"
DB_PASS="admin_password"
DB_NAME="prestashop"
CONTAINER="agrochowski_db"
API_KEY="e44a97fbf306a8059ab8d633a7e55e49" 

# Generate a random key if not provided or default
if [ "$API_KEY" == "YOUR_GENERATED_KEY" ]; then
    API_KEY=$(openssl rand -hex 16 | tr 'a-z' 'A-Z')
fi

echo "Enabling Webservice and creating API Key: $API_KEY"

# SQL to enable webservice and add key
SQL="
UPDATE ps_configuration SET value = '1' WHERE name = 'PS_WEBSERVICE';

DELETE FROM ps_webservice_account WHERE \`key\` = '$API_KEY';
INSERT INTO ps_webservice_account (\`key\`, description, class_name, is_module, active) VALUES ('$API_KEY', 'Initializer Key', '', 0, 1);

SET @id_account = (SELECT id_webservice_account FROM ps_webservice_account WHERE \`key\` = '$API_KEY');

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
SELECT 'shops', 'GET', @id_account;
"

# Execute SQL in docker container
docker exec -i $CONTAINER mysql -u$DB_USER -p$DB_PASS $DB_NAME <<< "$SQL"

if [ $? -eq 0 ]; then
    echo "Successfully enabled Webservice and added API Key."
    echo "API Key: $API_KEY"
    echo "Please export this key before running the initializer:"
    echo "export PRESTASHOP_API_KEY=$API_KEY"
else
    echo "Failed to execute SQL."
fi
