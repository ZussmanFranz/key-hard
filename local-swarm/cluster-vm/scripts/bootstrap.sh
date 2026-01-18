#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

# Basic packages
apt-get update -y
apt-get install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release \
  apt-transport-https \
  jq \
  net-tools

# Docker installation
install -m 0755 -d /etc/apt/keyrings
if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
fi

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl restart docker

# Allow vagrant user to use docker
usermod -aG docker vagrant

# Disable ufw to simplify local networking (optional)
if systemctl is-enabled --quiet ufw; then
  systemctl disable --now ufw || true
fi

# Add host entries for cluster
HOSTS_MARKER="# local-swarm-cluster"
if ! grep -q "$HOSTS_MARKER" /etc/hosts; then
  cat <<'EOF' >> /etc/hosts
# local-swarm-cluster
192.168.56.10 bastion.local bastion
192.168.56.11 student-swarm01.local student-swarm01
192.168.56.12 student-swarm02.local student-swarm02
192.168.56.13 student-swarm03.local student-swarm03
192.168.56.14 student-swarm04.local student-swarm04
EOF
fi

# Kernel params for swarm overlay
modprobe br_netfilter || true
cat <<'EOF' >/etc/sysctl.d/99-swarm.conf
net.bridge.bridge-nf-call-iptables=1
net.bridge.bridge-nf-call-ip6tables=1
net.ipv4.ip_forward=1
EOF
sysctl --system
