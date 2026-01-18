# Local Swarm VM Cluster

This folder provisions a local Docker Swarm cluster that mirrors the original student cluster:
- 1 bastion VM for SSH jump
- 4 swarm nodes (1 manager + 3 workers)
- Docker Swarm orchestration
- Optional shared DB stack (Postgres, MySQL, MongoDB)

## Topology

- Bastion: `192.168.56.10` (bastion.local)
- Manager: `192.168.56.11` (student-swarm01.local)
- Worker 1: `192.168.56.12` (student-swarm02.local)
- Worker 2: `192.168.56.13` (student-swarm03.local)
- Worker 3: `192.168.56.14` (student-swarm04.local)

## Prerequisites (host machine)

- VirtualBox
- Vagrant
- 8 GB RAM free (min), 40 GB disk free

## Create the VM cluster

From this folder:

1) Start all VMs:

- `vagrant up`

2) SSH to bastion:

- `vagrant ssh bastion`

3) From bastion, SSH to manager (use the Vagrant private key):

- `ssh -i /vagrant/.vagrant/machines/swarm01/virtualbox/private_key vagrant@student-swarm01`

Alternative from the host (skips bastion):

- `vagrant ssh swarm01`

4) Validate swarm:

- `docker node ls`

## Shared DB stack (optional)

Deploy common DB services on the manager:

- `docker stack deploy -c /vagrant/stack-shared-db.yml admin-mysql`

Services/ports (host mode on manager):
- Postgres: 5432 (user: student, pass: student)
- MySQL: 3306 (root pass: student)
- Adminer: 9099 (web UI)
- MongoDB: 27017 (root: student)
- mongo-express: 8081

## Deploy your stack (example)

On manager:

- `docker stack deploy -c /vagrant/../../config/docker-compose-prod.yml BE_201253 --with-registry-auth`

## Access pattern (mirrors original)

- Use bastion as SSH jump host
- Use `student-swarm01` for swarm management commands
- Any published port is reachable on any node IP

## Notes

- VMs use host-only network `192.168.56.0/24`.
- Docker overlay network `agro_net` is created on the manager.
- You can destroy the cluster with `vagrant destroy -f`.
