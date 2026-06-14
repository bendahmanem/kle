#!/bin/bash
# create-index.sh — Cree un index avec mapping personnalise

set -e

ES_HOST="${ES_HOST:-localhost:9200}"
INDEX_NAME="${1:-students}"

echo "=== Creation de l'index '$INDEX_NAME' ==="

# Supprimer si existant
curl -s -X DELETE "http://${ES_HOST}/${INDEX_NAME}" | python3 -m json.tool 2>/dev/null || true

# Creer l'index avec mapping
curl -s -X PUT "http://${ES_HOST}/${INDEX_NAME}" \
  -H "Content-Type: application/json" \
  -d '{
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0,
      "index.refresh_interval": "1s"
    },
    "mappings": {
      "properties": {
        "name": { "type": "text" },
        "email": { "type": "keyword" },
        "age": { "type": "integer" },
        "promo": { "type": "keyword" },
        "created_at": { "type": "date" }
      }
    }
  }' | python3 -m json.tool

echo ""
echo "=== Index cree. Verification ==="
curl -s -X GET "http://${ES_HOST}/${INDEX_NAME}/_mapping?pretty" | python3 -m json.tool