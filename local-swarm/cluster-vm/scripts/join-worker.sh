#!/usr/bin/env bash
set -euo pipefail

MANAGER_IP="192.168.56.11"
TOKEN_FILE="/vagrant/join-token"

if docker info --format '{{.Swarm.LocalNodeState}}' | grep -q active; then
  exit 0
fi

# Wait for token file from manager
for i in {1..60}; do
  if [ -f "$TOKEN_FILE" ]; then
    break
  fi
  sleep 2
done

if [ ! -f "$TOKEN_FILE" ]; then
  echo "Join token not found at $TOKEN_FILE" >&2
  exit 1
fi

JOIN_TOKEN=$(cat "$TOKEN_FILE")

# Join swarm as worker
if ! docker info --format '{{.Swarm.LocalNodeState}}' | grep -q active; then
  docker swarm join --token "$JOIN_TOKEN" "$MANAGER_IP:2377"
fi
