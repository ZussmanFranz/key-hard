#!/bin/bash
set -e

echo "Starting PrestaShop with automatic theme configuration..."

# Run the theme initialization script in the background
# This will wait for PrestaShop to be installed and then configure the theme
# Output is logged to /tmp/init-theme.log for debugging
(nohup /tmp/init-theme.sh > /tmp/init-theme.log 2>&1 &)

echo "Theme initialization script started in background (logs at /tmp/init-theme.log)"

# Execute the original PrestaShop entrypoint
# The original image uses /tmp/docker_run.sh as entrypoint
exec /tmp/docker_run.sh "$@"
