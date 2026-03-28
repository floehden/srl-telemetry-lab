#!/bin/bash

echo "Configuring IPs for Cluster 1 (Leaf 1)..."
docker exec c1-control-plane ip addr add 172.17.0.11/24 dev eth1
docker exec c1-control-plane ip link set eth1 up
docker exec c1-worker ip addr add 172.17.0.12/24 dev eth1
docker exec c1-worker ip link set eth1 up
docker exec c1-worker2 ip addr add 172.17.0.13/24 dev eth1
docker exec c1-worker2 ip link set eth1 up

echo "Configuring IPs for Cluster 2 (Leaf 2)..."
docker exec c2-control-plane ip addr add 172.17.0.21/24 dev eth1
docker exec c2-control-plane ip link set eth1 up
docker exec c2-worker ip addr add 172.17.0.22/24 dev eth1
docker exec c2-worker ip link set eth1 up
docker exec c2-worker2 ip addr add 172.17.0.23/24 dev eth1
docker exec c2-worker2 ip link set eth1 up

echo "Configuring IPs for Cluster 3 (Leaf 3)..."
docker exec c3-control-plane ip addr add 172.17.0.31/24 dev eth1
docker exec c3-control-plane ip link set eth1 up
docker exec c3-worker ip addr add 172.17.0.32/24 dev eth1
docker exec c3-worker ip link set eth1 up
docker exec c3-worker2 ip addr add 172.17.0.33/24 dev eth1
docker exec c3-worker2 ip link set eth1 up

echo "All Kind nodes successfully configured on the EVPN fabric!"