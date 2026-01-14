#!/bin/bash
set -e

echo "Theme initialization script started at $(date)"

# Wait for PrestaShop to be fully installed
while [ ! -f /var/www/html/config/settings.inc.php ]; do
    echo "Waiting for PrestaShop installation to complete..."
    sleep 5
done

echo "PrestaShop config found, waiting for installation to finalize..."

# Wait for the ps_shop table to exist and have data
until mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -N -e "SELECT theme_name FROM ps_shop LIMIT 1;" > /dev/null 2>&1; do
    echo "Database tables not ready yet, waiting..."
    sleep 5
done

# Wait for install.lock file which indicates installation is complete
while [ ! -f /var/www/html/install.lock ]; do
    echo "Waiting for installation to finish (install.lock)..."
    sleep 5
done

# Wait for modules to be installed
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

sleep 5

echo "=== Configuring modules ==="
# Instead of importing module tables (which breaks routing), we disable unwanted modules
# and configure hooks selectively

# Disable unwanted modules that show on homepage
echo "Disabling unwanted modules..."
mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -e "
    UPDATE ps_module SET active = 0 WHERE name IN (
        'ps_banner',
        'ps_customtext', 
        'ps_emailsubscription',
        'ps_socialfollow',
        'ps_imageslider'
    );
" 2>/dev/null && echo "Unwanted modules disabled"

# Keep ps_linklist enabled to avoid admin routing errors
mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -e "
    UPDATE ps_module SET active = 1 WHERE name = 'ps_linklist';
" 2>/dev/null && echo "ps_linklist kept enabled"

# Remove hooks for disabled modules so they don't appear
echo "Removing hooks for disabled modules..."
mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -e "
    DELETE hm FROM ps_hook_module hm
    JOIN ps_module m ON hm.id_module = m.id_module
    WHERE m.active = 0;
" 2>/dev/null && echo "Hooks cleaned up"

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

# Check current theme and update if needed
CURRENT_THEME=$(mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -N -e "SELECT theme_name FROM ps_shop WHERE id_shop = 1;" 2>/dev/null)
echo "Current theme: $CURRENT_THEME"

if [ "$CURRENT_THEME" != "agrochowski" ]; then
    echo "Changing theme from '$CURRENT_THEME' to 'agrochowski'..."
    mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -e \
        "UPDATE ps_shop SET theme_name = 'agrochowski' WHERE id_shop = 1;" 2>&1
    echo "Theme updated"
fi

echo "=== Removing install folder ==="
if [ -d /var/www/html/install ]; then
    rm -rf /var/www/html/install
    echo "Install folder removed"
fi

echo "=== Finding admin panel URL ==="
ADMIN_FOLDER=$(ls -d /var/www/html/admin*/ 2>/dev/null | head -1 | xargs basename)
if [ -n "$ADMIN_FOLDER" ]; then
    echo "==========================================="
    echo "ADMIN PANEL URL: https://localhost:8443/${ADMIN_FOLDER}/"
    echo "==========================================="
fi

echo "=== Clearing PrestaShop cache ==="
rm -rf /var/www/html/var/cache/prod/* 2>/dev/null || true
rm -rf /var/www/html/var/cache/dev/* 2>/dev/null || true
chown -R www-data:www-data /var/www/html/var
chmod -R 775 /var/www/html/var

echo "=== Enabling Webservice API ==="
mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -e \
    "UPDATE ps_configuration SET value = '1' WHERE name = 'PS_WEBSERVICE';" 2>/dev/null || true

echo "=== Configuring Main Menu ==="
MENU_CATS=$(mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -N -e \
    "SELECT GROUP_CONCAT(CONCAT('CAT', id_category) SEPARATOR ',') FROM ps_category WHERE id_parent = 2 AND active = 1;" 2>/dev/null)

if [ -n "$MENU_CATS" ] && [ "$MENU_CATS" != "NULL" ]; then
    echo "Setting main menu categories: $MENU_CATS"
    mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -e \
        "UPDATE ps_configuration SET value = '$MENU_CATS' WHERE name = 'MOD_BLOCKTOPMENU_ITEMS';" 2>/dev/null || true
fi

echo "=== Configuring Featured Products ==="
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
fi

echo "=== Final cache clear ==="
rm -rf /var/www/html/var/cache/prod/* 2>/dev/null || true
rm -rf /var/www/html/var/cache/dev/* 2>/dev/null || true
chown -R www-data:www-data /var/www/html/var

echo "Theme setup complete at $(date)!"
echo "Admin panel: https://localhost:8443/${ADMIN_FOLDER}/"
