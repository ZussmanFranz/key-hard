#!/bin/bash

cd config/
docker-compose down -v 
docker-compose up -d

echo "Waiting for PrestaShop to launch..."

URL="http://localhost:8080"
TIMEOUT=120
START=$(date +%s)

draw_progress_bar() {
    local width=50
    local percent=$1
    local filled=$((width * percent / 100))
    local empty=$((width - filled))
    
    printf "\r["
    for ((i=0; i<filled; i++)); do printf "#"; done
    for ((i=0; i<empty; i++)); do printf " "; done
    printf "] %d%%" "$percent"
}

while true; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
    
    if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "302" ]]; then
        draw_progress_bar 100
        echo -e "\nPrestaShop is ready at $URL"
        break
    fi

    NOW=$(date +%s)
    ELAPSED=$((NOW - START))
    
    if [ $ELAPSED -gt $TIMEOUT ]; then
        echo -e "\nTimeout waiting for PrestaShop to start."
        break
    fi
    
    PERCENT=$((ELAPSED * 100 / TIMEOUT))
    if [ $PERCENT -ge 100 ]; then PERCENT=99; fi
    
    draw_progress_bar $PERCENT
    sleep 2
done
