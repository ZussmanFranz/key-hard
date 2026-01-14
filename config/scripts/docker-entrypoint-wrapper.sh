#!/bin/bash
set -e

# Run the theme initialization script in the background
# This will wait for PrestaShop to be installed and then configure the theme
(/tmp/init-theme.sh &)

# Execute the original PrestaShop entrypoint
# The original image uses /tmp/docker_run.sh as entrypoint
exec /tmp/docker_run.sh "$@"
