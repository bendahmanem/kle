#!/bin/bash
# index-document.sh — Indexe un document dans un index

set -e

ES_HOST="${ES_HOST:-localhost:9200}"
INDEX_NAME="${1:-students}"

echo "=== Indexation de documents dans '$INDEX_NAME' ==="

# Document 1
curl -s -X POST "http://${ES_HOST}/${INDEX_NAME}/_doc/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Martin",
    "email": "alice.martin@isitech.fr",
    "age": 21,
    "promo": "B2",
    "created_at": "2024-09-01T09:00:00Z"
  }' | python3 -m json.tool

# Document 2
curl -s -X POST "http://${ES_HOST}/${INDEX_NAME}/_doc/2" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bob Dupont",
    "email": "bob.dupont@isitech.fr",
    "age": 22,
    "promo": "B2",
    "created_at": "2024-09-02T10:30:00Z"
  }' | python3 -m json.tool

# Document 3
curl -s -X POST "http://${ES_HOST}/${INDEX_NAME}/_doc/3" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Claire Bernard",
    "email": "claire.bernard@isitech.fr",
    "age": 20,
    "promo": "B1",
    "created_at": "2024-09-03T14:15:00Z"
  }' | python3 -m json.tool

echo ""
echo "=== Recherche: tous les etudiants B2 ==="
curl -s -X GET "http://${ES_HOST}/${INDEX_NAME}/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "term": { "promo": "B2" }
    }
  }' | python3 -m json.tool

echo ""
echo "=== Recherche: age > 21 ==="
curl -s -X GET "http://${ES_HOST}/${INDEX_NAME}/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "range": { "age": { "gt": 21 } }
    }
  }' | python3 -m json.tool