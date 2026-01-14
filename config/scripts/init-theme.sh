#!/bin/bash
set -e

echo "Theme initialization script started at $(date)"

# Wait for PrestaShop to be fully installed
# The init script creates this file when installation is complete
while [ ! -f /var/www/html/config/settings.inc.php ]; do
    echo "Waiting for PrestaShop installation to complete..."
    sleep 5
done

echo "PrestaShop config found, waiting for installation to finalize..."

# Wait for the ps_shop table to exist and have data (means installation is complete)
echo "Waiting for database tables to be ready..."
until mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -N -e "SELECT theme_name FROM ps_shop LIMIT 1;" > /dev/null 2>&1; do
    echo "Database tables not ready yet, waiting..."
    sleep 5
done

# Wait for install.lock file which indicates installation is complete
while [ ! -f /var/www/html/install.lock ]; do
    echo "Waiting for installation to finish (install.lock)..."
    sleep 5
done

# CRITICAL: Wait for modules to be installed (this is the real indicator that installation is done)
echo "Waiting for modules to be installed..."
MODULE_COUNT=0
while [ "$MODULE_COUNT" -lt 10 ]; do
    MODULE_COUNT=$(mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -N -e "SELECT COUNT(*) FROM ps_module;" 2>/dev/null || echo "0")
    if [ "$MODULE_COUNT" -lt 10 ]; then
        echo "Modules not yet installed (count: $MODULE_COUNT), waiting..."
        sleep 10
    fi
done
echo "Modules installed (count: $MODULE_COUNT)"

# Extra wait to ensure installation is fully complete
sleep 5

echo "=== Setting up agrochowski theme ==="

# Fix permissions on theme directory
if [ -d /var/www/html/themes/agrochowski ]; then
    chown -R www-data:www-data /var/www/html/themes/agrochowski
    chmod -R 755 /var/www/html/themes/agrochowski
    echo "Theme directory permissions fixed"
else
    echo "ERROR: Theme directory /var/www/html/themes/agrochowski not found!"
    exit 1
fi

# Check current theme
CURRENT_THEME=$(mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -N -e "SELECT theme_name FROM ps_shop WHERE id_shop = 1;" 2>/dev/null)
echo "Current theme: $CURRENT_THEME"

if [ "$CURRENT_THEME" != "agrochowski" ]; then
    echo "Changing theme from '$CURRENT_THEME' to 'agrochowski'..."
    
    # Update the theme_name directly in ps_shop table
    mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -e \
        "UPDATE ps_shop SET theme_name = 'agrochowski' WHERE id_shop = 1;" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "Database updated successfully"
    else
        echo "Database update failed, trying alternative method..."
    fi
    
    # Verify the change
    NEW_THEME=$(mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -N -e "SELECT theme_name FROM ps_shop WHERE id_shop = 1;" 2>/dev/null)
    echo "Theme after update: $NEW_THEME"
else
    echo "agrochowski theme is already set"
fi

echo "=== Removing install folder ==="
# Remove the install folder to allow admin access
if [ -d /var/www/html/install ]; then
    rm -rf /var/www/html/install
    echo "Install folder removed successfully"
else
    echo "Install folder already removed"
fi

echo "=== Finding admin panel URL ==="
# Find the admin folder name
ADMIN_FOLDER=$(ls -d /var/www/html/admin*/ 2>/dev/null | head -1 | xargs basename)
if [ -n "$ADMIN_FOLDER" ]; then
    echo "==========================================="
    echo "ADMIN PANEL URL: https://localhost:8443/${ADMIN_FOLDER}/"
    echo "==========================================="
else
    echo "Warning: Could not find admin folder"
fi

echo "=== Clearing PrestaShop cache ==="
# Clear PrestaShop cache to apply theme changes
rm -rf /var/www/html/var/cache/prod/* 2>/dev/null || true
rm -rf /var/www/html/var/cache/dev/* 2>/dev/null || true

# Fix permissions on var directory
chown -R www-data:www-data /var/www/html/var
chmod -R 775 /var/www/html/var

echo "=== Enabling Webservice API ==="
# Enable webservice for API access (needed for initializer)
mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -e \
    "UPDATE ps_configuration SET value = '1' WHERE name = 'PS_WEBSERVICE';" 2>/dev/null || true

echo "=== Configuring Main Menu ==="
# Wait for categories to be created by initializer, then update menu
# For now, set a placeholder that will work with default structure
# The menu will be properly configured after products are initialized
# Default: show all top-level categories (children of root category 2)

# Get all top-level category IDs and build menu string
MENU_CATS=$(mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -N -e \
    "SELECT GROUP_CONCAT(CONCAT('CAT', id_category) SEPARATOR ',') FROM ps_category WHERE id_parent = 2 AND active = 1;" 2>/dev/null)

if [ -n "$MENU_CATS" ] && [ "$MENU_CATS" != "NULL" ]; then
    echo "Setting main menu categories: $MENU_CATS"
    mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -e \
        "UPDATE ps_configuration SET value = '$MENU_CATS' WHERE name = 'MOD_BLOCKTOPMENU_ITEMS';" 2>/dev/null || true
else
    echo "No custom categories found, keeping default menu"
fi

echo "=== Configuring Featured Products ==="
# Set featured products to show from the first top-level category with products
FEATURED_CAT=$(mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -N -e \
    "SELECT c.id_category FROM ps_category c 
     JOIN ps_category_product cp ON c.id_category = cp.id_category 
     WHERE c.id_parent = 2 AND c.active = 1 
     GROUP BY c.id_category 
     ORDER BY COUNT(cp.id_product) DESC 
     LIMIT 1;" 2>/dev/null)

if [ -n "$FEATURED_CAT" ] && [ "$FEATURED_CAT" != "NULL" ]; then
    echo "Setting featured products category: $FEATURED_CAT"
    mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -e \
        "UPDATE ps_configuration SET value = '$FEATURED_CAT' WHERE name = 'HOME_FEATURED_CAT';" 2>/dev/null || true
else
    echo "No categories with products found, keeping default featured category"
fi

echo "=== Final cache clear ==="
rm -rf /var/www/html/var/cache/prod/* 2>/dev/null || true
rm -rf /var/www/html/var/cache/dev/* 2>/dev/null || true
chown -R www-data:www-data /var/www/html/var

echo "Theme setup complete at $(date)!"
echo "Agrochowski theme should now be active."
echo "Admin panel: https://localhost:8443/${ADMIN_FOLDER}/"
