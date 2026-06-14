#!/bin/bash
# check-sys.sh — Verifie et configure vm.max_map_count

set -e

echo "=== vm.max_map_count actuel ==="
CURRENT=$(sysctl vm.max_map_count 2>/dev/null | awk '{print $3}')
echo "Valeur actuelle : $CURRENT"

if [ "$CURRENT" -ge 262144 ]; then
    echo "✅ Valeur suffisante (>= 262144)"
else
    echo "❌ Valeur insuffisante (< 262144)"
    echo ""
    echo "=== Configuration permanente ==="
    echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
    sudo sysctl -w vm.max_map_count=262144
    echo "✅ Applique pour cette session"
fi

echo ""
echo "=== Verification finale ==="
sysctl vm.max_map_count