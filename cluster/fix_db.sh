#!/bin/bash

# Konfiguracja Twojego zespołu
PREFIX="BE_201253"
DB_NAME="BE_201253"
DB_USER="root"
DB_PASS="student"
DB_HOST="admin-mysql_db"
PORT="20125"

# Adres IP węzła Managera (tu stoi sklep)
SHOP_DOMAIN="localhost"

echo "Szukanie kontenera Prestashop..."
PS_CONTAINER=""
for i in {1..204}; do
    PS_CONTAINER=$(docker ps -q -f name=${PREFIX}_prestashop)
    [ ! -z "$PS_CONTAINER" ] && break
    echo "Próba $i/204: Kontener jeszcze nie wstał..."
    sleep 5
done

if [ -z "$PS_CONTAINER" ]; then
    echo "BŁĄD: Kontener Prestashop nie uruchomił się."
    exit 1
fi

echo "Konfiguracja plików wewnątrz kontenera ($PS_CONTAINER)..."
echo "Kopiowanie modułów z backupu..."
docker cp ./modules_backup/. $PS_CONTAINER:/var/www/html/modules
echo "Moduły skopiowane."
docker exec -u 0 -i $PS_CONTAINER bash <<EOF
# 1. NAPRAWA UPRAWNIEŃ (Kluczowe po ręcznym kopiowaniu jako root!)
# Skoro wrzuciłeś moduły ręcznie, musimy oddać je użytkownikowi www-data
chown -R www-data:www-data /var/www/html/modules
chown -R www-data:www-data /var/www/html/var
chmod -R 775 /var/www/html/var

# 2. USUWANIE PRZEKIEROWAŃ
# Usuwamy .htaccess, bo wymusza HTTPS
#rm -f /var/www/html/.htaccess
#echo "Usunięto plik .htaccess"

# Konfiguracja bazy w parameters.php
FILE="/var/www/html/app/config/parameters.php"
if [ -f "\$FILE" ]; then
    sed -i "s/'database_host' => '.*'/'database_host' => '$DB_HOST'/" \$FILE
    sed -i "s/'database_name' => '.*'/'database_name' => '$DB_NAME'/" \$FILE
    sed -i "s/'database_user' => '.*'/'database_user' => '$DB_USER'/" \$FILE
    sed -i "s/'database_password' => '.*'/'database_password' => '$DB_PASS'/" \$FILE
fi


# Czyszczenie cache
rm -rf /var/www/html/var/cache/*
EOF

echo "Wyłączanie SSL i ustawianie domeny w bazie danych..."
DB_CONTAINER=$(docker ps -q -f name=admin-mysql_db)

if [ ! -z "$DB_CONTAINER" ]; then
    docker exec -i $DB_CONTAINER mysql -u$DB_USER -p$DB_PASS $DB_NAME <<EOF
/* Ustawienie poprawnego IP i portu */
UPDATE ps_configuration SET value='$SHOP_DOMAIN:$PORT' WHERE name IN ('PS_SHOP_DOMAIN', 'PS_SHOP_DOMAIN_SSL');
UPDATE ps_shop_url SET domain='$SHOP_DOMAIN:$PORT', domain_ssl='$SHOP_DOMAIN:$PORT';

/* BEZWZGLĘDNE WYŁĄCZENIE SSL */
UPDATE ps_configuration SET value='0' WHERE name='PS_SSL_ENABLED';
UPDATE ps_configuration SET value='0' WHERE name='PS_SSL_ENABLED_EVERYWHERE';
UPDATE ps_configuration SET value='0' WHERE name='PS_REWRITING_SETTINGS';
EOF
    echo "Baza zaktualizowana."
else
    echo "OSTRZEŻENIE: Nie znaleziono bazy danych."
fi

echo "-------------------------------------------------------"
echo "GOTOWE! Wejdź w trybie INCOGNITO na adres:"
echo "http://$SHOP_DOMAIN:$PORT"