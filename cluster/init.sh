#!/bin/bash
set -e

# W Twoim docker-compose usługa nazywa się 'prestashop'.
# W Swarmie nazwa kontenera będzie zawierać nazwę stacka i usługi, np. be123_prestashop.1.xxxxx
SERVICE_SUFFIX="_prestashop"

# Funkcja szukająca ID kontenera
get_container_id() {
    # Szukamy czegokolwiek co ma "_prestashop" w nazwie i jest uruchomione
    local id=$(docker ps --filter "name=${SERVICE_SUFFIX}" --format "{{.ID}}" | head -n 1)
    
    if [ -z "$id" ]; then
        echo -e "\e[31mBŁĄD: Nie znaleziono kontenera Prestashop na tym węźle.\e[0m"
        echo "Upewnij się, że:"
        echo "1. Stack jest uruchomiony (docker stack ls)"
        echo "2. Jesteś na serwerze, gdzie fizycznie stoi kontener (docker node ps)"
        exit 1
    fi
    echo "$id"
}

CONTAINER_ID=$(get_container_id)
echo -e "\e[32mZnaleziono kontener: $CONTAINER_ID\e[0m"

# 1. Tworzymy folder tymczasowy w kontenerze
docker exec "$CONTAINER_ID" mkdir -p /tmp/import

# 2. Kopiujemy pliki z hosta do kontenera
echo "Kopiowanie plików..."
docker cp importer.php "$CONTAINER_ID":/tmp/import/
docker cp categories.json "$CONTAINER_ID":/tmp/import/
docker cp products.json "$CONTAINER_ID":/tmp/import/

# 3. Uruchamiamy importer PHP
echo "Uruchamianie importu..."
# Używamy flagi -d memory_limit=512M dla pewności, choć jest też w skrypcie
docker exec "$CONTAINER_ID" php -d memory_limit=512M -f /tmp/import/importer.php

# 4. Sprzątanie po sobie
echo "Czyszczenie plików tymczasowych..."
docker exec "$CONTAINER_ID" rm -rf /tmp/import

echo -e "\e[32mGotowe!\e[0m"