#!/bin/bash
set -e

# Nazwa usługi (fragment nazwy kontenera)
SERVICE_SUFFIX="_prestashop"

# Funkcja szukająca ID kontenera
get_container_id() {
    local id=$(docker ps --filter "name=${SERVICE_SUFFIX}" --format "{{.ID}}" | head -n 1)
    if [ -z "$id" ]; then
        echo "BŁĄD: Nie znaleziono kontenera Prestashop na tym węźle."
        exit 1
    fi
    echo "$id"
}

CONTAINER_ID=$(get_container_id)
echo "Znaleziono kontener: $CONTAINER_ID"

# 1. Tworzenie folderu tymczasowego
docker exec "$CONTAINER_ID" mkdir -p /tmp/fix

# 2. Kopiowanie skryptu naprawczego
echo "Kopiowanie skryptu..."
docker cp fix_main_menu.php "$CONTAINER_ID":/tmp/fix/

# 3. Uruchomienie
echo "Uruchamianie naprawy..."
docker exec "$CONTAINER_ID" php -f /tmp/fix/fix_main_menu.php

# 4. Sprzątanie
docker exec "$CONTAINER_ID" rm -rf /tmp/fix

echo "Gotowe!"