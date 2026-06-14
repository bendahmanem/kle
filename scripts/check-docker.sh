#!/bin/bash
# check-docker.sh — Verifie que Docker est installe et tourne

set -e

echo "=== Docker version ==="
docker --version

echo ""
echo "=== Docker Compose version ==="
docker-compose --version 2>/dev/null || docker compose version

echo ""
echo "=== Docker daemon running? ==="
if docker ps &>/dev/null; then
    echo "✅ Docker is running"
else
    echo "❌ Docker daemon is NOT running. Start Docker Desktop or run: sudo systemctl start docker"
    exit 1
fi

echo ""
echo "=== Containers running (should be empty initially) ==="
docker ps

echo ""
echo "=== Docker info (RAM allocated) ==="
docker info | grep -E "MemTotal|Memory|Limit"

echo ""
echo "✅ Docker est pret."