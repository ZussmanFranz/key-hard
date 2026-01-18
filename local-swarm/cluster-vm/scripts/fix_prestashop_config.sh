#!/usr/bin/env bash
set -euo pipefail

STACK_NAME=${1:-BE_201253}
DB_HOST=${2:-admin-mysql_db}
DB_NAME=${3:-BE_201253}
DB_USER=${4:-root}
DB_PASS=${5:-student}
DB_PREFIX=${6:-ps_}

SECRET=$(openssl rand -hex 16 2>/dev/null || cat /proc/sys/kernel/random/uuid | tr -d '-')
CREATION_DATE=$(date -u +%Y-%m-%d)

CONTAINER_ID=$(docker ps --filter "name=${STACK_NAME}_prestashop" -q | head -n1)
if [ -z "$CONTAINER_ID" ]; then
  echo "PrestaShop container not found for stack ${STACK_NAME}" >&2
  exit 1
fi

cat <<EOF | docker exec -i "$CONTAINER_ID" sh -c "cat > /var/www/html/app/config/parameters.php"
<?php return array (
  'parameters' =>
  array (
    'database_host' => '${DB_HOST}',
    'database_port' => '',
    'database_name' => '${DB_NAME}',
    'database_user' => '${DB_USER}',
    'database_password' => '${DB_PASS}',
    'database_prefix' => '${DB_PREFIX}',
    'database_engine' => 'InnoDB',
    'mailer_transport' => 'smtp',
    'mailer_host' => '127.0.0.1',
    'mailer_user' => NULL,
    'mailer_password' => NULL,
    'secret' => '${SECRET}',
    'ps_caching' => 'CacheMemcache',
    'ps_cache_enable' => false,
    'ps_creation_date' => '${CREATION_DATE}',
    'locale' => 'pl-PL',
  ),
);
EOF

echo "parameters.php written in container ${CONTAINER_ID}."