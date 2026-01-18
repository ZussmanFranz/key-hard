#!/usr/bin/env bash
set -euo pipefail

MANAGER_IP="192.168.56.11"
TOKEN_FILE="/vagrant/join-token"

# Wait for Docker daemon
for i in {1..60}; do
  if docker info >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon not ready" >&2
  exit 1
fi

# Initialize swarm (retry if needed)
if ! docker info --format '{{.Swarm.LocalNodeState}}' | grep -q active; then
  for i in {1..5}; do
    if docker swarm init --advertise-addr "$MANAGER_IP"; then
      break
    fi
    sleep 2
  done
fi

if ! docker info --format '{{.Swarm.LocalNodeState}}' | grep -q active; then
  echo "Swarm init failed" >&2
  exit 1
fi

# Create default overlay network used by stacks
if ! docker network ls --format '{{.Name}}' | grep -q '^agro_net$'; then
  docker network create --driver overlay --attachable agro_net
fi

# Write worker join token for other nodes
JOIN_TOKEN=$(docker swarm join-token -q worker)
echo "$JOIN_TOKEN" > "$TOKEN_FILE"
chmod 644 "$TOKEN_FILE"
