#!/bin/bash
set -e

SERVICE_SUFFIX="_prestashop"

get_container_id() {
    local id=$(docker ps --filter "name=${SERVICE_SUFFIX}" --format "{{.ID}}" | head -n 1)
    if [ -z "$id" ]; then
        echo "BŁĄD: Nie znaleziono kontenera Prestashop."
        exit 1
    fi
    echo "$id"
}

CONTAINER_ID=$(get_container_id)
echo "Znaleziono kontener: $CONTAINER_ID"

echo "Szukanie niestandardowego obrazka banera i aktualizacja bazy..."

cat <<EOF > force_banner_internal.php
<?php
if (php_sapi_name() !== 'cli') { exit; }

\$_SERVER['HTTP_HOST'] = 'localhost:20125';
define('_PS_ROOT_DIR_', '/var/www/html');
require_once(_PS_ROOT_DIR_ . '/config/config.inc.php');
require_once(_PS_ROOT_DIR_ . '/init.php');

// 1. Znajdź plik obrazka w folderze modułu
\$bannerDir = _PS_ROOT_DIR_ . '/modules/ps_banner/img/';
\$files = scandir(\$bannerDir);
\$targetFile = '';
\$newestTime = 0;

foreach (\$files as \$file) {
    if (\$file === '.' || \$file === '..' || \$file === 'index.php') continue;
    // Ignoruj domyślny plik Presty
    if (\$file === 'sale70.png') continue;
    
    // Szukamy czegokolwiek co jest obrazkiem
    if (preg_match('/\.(jpg|jpeg|png|gif)$/i', \$file)) {
        \$filePath = \$bannerDir . \$file;
        // Wybieramy najnowszy wgrany plik
        if (filemtime(\$filePath) > \$newestTime) {
            \$newestTime = filemtime(\$filePath);
            \$targetFile = \$file;
        }
    }
}

if (!empty(\$targetFile)) {
    echo " >> Znaleziono Twój baner: " . \$targetFile . "\n";
    
    // Pobierz wszystkie języki
    \$languages = Language::getLanguages(false);
    \$langConfig = [];
    foreach (\$languages as \$lang) {
        \$langConfig[\$lang['id_lang']] = \$targetFile;
    }

    // 2. Aktualizacja konfiguracji
    // Ustawiamy ten sam plik dla WSZYSTKICH języków
    Configuration::updateValue('BANNER_IMG', \$langConfig);
    
    // Dodatkowo wymuszamy aktualizację dla wszystkich kontekstów sklepów
    \$shops = Shop::getShops(true, null, true);
    foreach (\$shops as \$shopId) {
        Configuration::updateValue('BANNER_IMG', \$langConfig, false, null, \$shopId);
    }
    
    // Ustawiamy link banera na stronę główną (dla wszystkich języków)
    \$linkConfig = [];
    foreach (\$languages as \$lang) {
        \$linkConfig[\$lang['id_lang']] = 'https://' . \$_SERVER['HTTP_HOST'];
    }
    Configuration::updateValue('BANNER_LINK', \$linkConfig);

    echo " >> Zaktualizowano BANNER_IMG dla wszystkich języków (" . count(\$languages) . ") i sklepów.\n";
} else {
    echo " !! Nie znaleziono nowego pliku banera (innego niż sale70.png) w folderze modułu.\n";
}

// 3. Czyszczenie cache
Tools::clearSmartyCache();
Tools::clearXMLCache();
Media::clearCache();
echo " >> Cache wyczyszczony.\n";
?>
EOF

# Wgrywanie i uruchamianie
docker cp force_banner_internal.php "$CONTAINER_ID":/tmp/force_banner_internal.php
# Uruchamiamy jako www-data aby mieć pewność co do uprawnień odczytu
docker exec -u www-data "$CONTAINER_ID" php -f /tmp/force_banner_internal.php

# Sprzątanie
docker exec -u 0 "$CONTAINER_ID" rm /tmp/force_banner_internal.php
rm force_banner_internal.php

echo "Gotowe. Odśwież stronę (Ctrl+F5)."