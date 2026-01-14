#!/bin/bash
set -e

# Wait for PrestaShop to be fully installed
# The init script creates this file when installation is complete
while [ ! -f /var/www/html/config/settings.inc.php ]; do
    echo "Waiting for PrestaShop installation to complete..."
    sleep 5
done

# Additional wait for database to be ready
sleep 10

echo "Setting up agrochowski theme..."

# Fix permissions on var directory
chown -R www-data:www-data /var/www/html/var
chmod -R 775 /var/www/html/var

# Fix permissions on theme directory
if [ -d /var/www/html/themes/agrochowski ]; then
    chown -R www-data:www-data /var/www/html/themes/agrochowski
    chmod -R 755 /var/www/html/themes/agrochowski
fi

# Enable and set agrochowski as the default theme
# First check if the theme is already enabled
CURRENT_THEME=$(php /var/www/html/bin/console prestashop:theme:list 2>/dev/null | grep -o 'agrochowski.*true' || echo "")

if [ -z "$CURRENT_THEME" ]; then
    echo "Enabling agrochowski theme..."
    php /var/www/html/bin/console prestashop:theme:enable agrochowski || {
        echo "Warning: Could not enable theme via console, attempting database update..."
        # Fallback: directly update the database
        mysql -h ${DB_SERVER} -u ${DB_USER} -p${DB_PASSWD} ${DB_NAME} -e \
            "UPDATE ps_shop SET id_theme = (SELECT id_theme FROM ps_theme WHERE name = 'agrochowski') WHERE id_shop = 1;" 2>/dev/null || true
    }
else
    echo "agrochowski theme is already enabled"
fi

# Clear PrestaShop cache
echo "Clearing cache..."
rm -rf /var/www/html/var/cache/* 2>/dev/null || true

echo "Theme setup complete!"
