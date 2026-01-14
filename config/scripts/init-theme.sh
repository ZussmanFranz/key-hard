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

# Extra wait to ensure installation is fully complete
sleep 15

echo "Setting up agrochowski theme..."

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

# Clear PrestaShop cache to apply theme changes
echo "Clearing cache..."
rm -rf /var/www/html/var/cache/prod/* 2>/dev/null || true
rm -rf /var/www/html/var/cache/dev/* 2>/dev/null || true

# Fix permissions on var directory
chown -R www-data:www-data /var/www/html/var
chmod -R 775 /var/www/html/var

echo "Theme setup complete at $(date)! Agrochowski theme should now be active."
