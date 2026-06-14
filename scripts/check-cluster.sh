#!/bin/bash
# check-cluster.sh — Verifie la sante du cluster Elasticsearch

set -e

ES_HOST="${ES_HOST:-localhost:9200}"

echo "=== Sante du cluster ==="
curl -s -X GET "http://${ES_HOST}/_cat/health?v&pretty"

echo ""
echo "=== Version Elasticsearch ==="
curl -s -X GET "http://${ES_HOST}" | python3 -m json.tool 2>/dev/null | grep -E '"name"|"version"|"cluster_name"|"build_flavor"|"build_type"'

echo ""
echo "=== Nodes ==="
curl -s -X GET "http://${ES_HOST}/_cat/nodes?v&pretty"

echo ""
echo "=== Indices ==="
curl -s -X GET "http://${ES_HOST}/_cat/indices?v&pretty"

echo ""
echo "=== Health check passed ==="