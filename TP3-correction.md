# TP3 - Correction : Recherche geospatiale Airbnb avec optimisations avancees

> **Module ELK - Chapitre 2** | Version Elastic : 9.4.2 | Duree : 3-4h

---

## Preparation

```bash
# Verifier que la stack ELK du TP1 tourne
./scripts/check-cluster.sh

# Installer les dependances Python
pip install pandas requests faker
```

---

## Partie 1 : Preparation du dataset

### 1.1 - Generer le dataset

```bash
# Generer 50 000 listings multi-villes
python3 scripts/tp3-airbnb-dataset.py --count 50000 --output airbnb-listings.json

# Verifier le fichier genere
wc -l airbnb-listings.json
head -1 airbnb-listings.json | python3 -m json.tool | head -20
```

Le script genere des listings pour : **Paris, New York, Londres, Barcelona, Amsterdam** avec :
- Geolocalisation reelle (lat/lon dans un rayon de ~8km du centre-ville)
- Donnees host, amenities, reviews, prix en EUR/USD/GBP
- Superhosts (~25% des hosts)

---

## Partie 2 : Creer l'index avec mapping geospatial

### 2.1 - Supprimer l'index existant

```bash
curl -X DELETE "localhost:9200/airbnb-listings" 2>/dev/null || true
```

### 2.2 - Creer l'index avec mapping complet

```bash
curl -X PUT "localhost:9200/airbnb-listings" \
  -H "Content-Type: application/json" \
  -d '{
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 0,
    "refresh_interval": "30s",
    "max_result_window": 50000
  },
  "mappings": {
    "properties": {
      "listing_id": { "type": "keyword" },
      "name": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "description": { "type": "text" },
      "host": {
        "properties": {
          "host_id": { "type": "keyword" },
          "host_name": { "type": "keyword" },
          "host_since": { "type": "date" },
          "host_response_rate": { "type": "byte" },
          "host_is_superhost": { "type": "boolean" }
        }
      },
      "location": { "type": "geo_point" },
      "address": {
        "properties": {
          "street": { "type": "text" },
          "city": { "type": "keyword" },
          "country": { "type": "keyword" },
          "zipcode": { "type": "keyword" },
          "neighborhood": { "type": "keyword", "fields": { "text": { "type": "text" } } }
        }
      },
      "property_type": { "type": "keyword" },
      "room_type": { "type": "keyword" },
      "accommodates": { "type": "integer" },
      "bedrooms": { "type": "integer" },
      "beds": { "type": "integer" },
      "bathrooms": { "type": "half_float" },
      "amenities": { "type": "keyword" },
      "price": { "type": "float" },
      "currency": { "type": "keyword" },
      "minimum_nights": { "type": "short" },
      "maximum_nights": { "type": "short" },
      "availability_365": { "type": "short" },
      "number_of_reviews": { "type": "integer" },
      "rating": { "type": "half_float" },
      "reviews": {
        "type": "nested",
        "properties": {
          "review_id": { "type": "keyword" },
          "reviewer_name": { "type": "keyword" },
          "date": { "type": "date" },
          "rating": { "type": "byte" },
          "comment": { "type": "text" }
        }
      },
      "instant_bookable": { "type": "boolean" },
      "cancellation_policy": { "type": "keyword" },
      "created_at": { "type": "date" },
      "last_updated": { "type": "date" }
    }
  }
}'
```

### 2.3 - Verifier le mapping

```bash
curl -s "localhost:9200/airbnb-listings/_mapping" | python3 -m json.tool | grep -A2 '"location"'
```

**Reponse attendue** : `"location" : { "type" : "geo_point" }`

### 2.4 - Tester le geo_point

```bash
curl -X POST "localhost:9200/airbnb-listings/_doc/test" \
  -H "Content-Type: application/json" \
  -d '{
    "listing_id": "test",
    "name": "Test listing",
    "location": { "lat": 48.8566, "lon": 2.3522 },
    "price": 100,
    "rating": 4.5
  }'

curl -s -X POST "localhost:9200/airbnb-listings/_refresh"

curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "geo_distance": {
        "distance": "1km",
        "location": { "lat": 48.8566, "lon": 2.3522 }
      }
    }
  }' | python3 -m json.tool | grep -E '"name"|"took"'
```

**Si "test" apparait → geo_point OK** ✅

---

## Partie 3 : Indexation du dataset

### 3.1 - Indexer en masse

```bash
# Avec curl et jq (si dispo)
curl -s -X POST "localhost:9200/_bulk" \
  --data-binary "$(cat airbnb-listings.json | jq -c '. | {index: {_index: "airbnb-listings", _id: .listing_id}}, doc: .}' )" \
  -H "Content-Type: application/x-ndjson"

# Methode plus simple : script Python d'indexation
python3 - << 'EOF'
import json, requests

ES = "http://localhost:9200"
INDEX = "airbnb-listings"
BATCH = 1000

with open("airbnb-listings.json") as f:
    lines = f.readlines()

total = len(lines)
for i in range(0, total, BATCH):
    batch = lines[i:i+BATCH]
    body = ""
    for line in batch:
        doc = json.loads(line)
        body += json.dumps({"index": {"_index": INDEX, "_id": doc["listing_id"]}}) + "\n"
        body += json.dumps(doc) + "\n"

    r = requests.post(f"{ES}/_bulk", data=body.encode(), headers={"Content-Type": "application/x-ndjson"})
    done = min(i + BATCH, total)
    print(f"  {done}/{total} ({100*done//total}%)", end="\r")

print(f"\nDone — {total} documents indexes")
EOF
```

### 3.2 - Verifier le count

```bash
curl -s "localhost:9200/airbnb-listings/_count"
```

**Resultat attendu** : `{"count": 50000}`

### 3.3 - Optimiser apres indexation

```bash
# Remettre refresh_interval a 1s
curl -X PUT "localhost:9200/airbnb-listings/_settings" \
  -H "Content-Type: application/json" \
  -d '{"index": {"refresh_interval": "1s"}}'

# Forcemerge pour reduire les segments
curl -X POST "localhost:9200/airbnb-listings/_forcemerge?max_num_segments=1&flush=true"

# Refresh final
curl -X POST "localhost:9200/airbnb-listings/_refresh"
```

### 3.4 - Statistiques

```bash
curl -s "localhost:9200/airbnb-listings/_stats?human" | python3 -m json.tool | grep -E '"docs"|"store"|"segments"'
```

---

## Partie 4 : Recherches geospatiales

### 4.1 - Recherche par distance

**Logements dans un rayon de 2 km autour de la Tour Eiffel (48.8584°N, 2.2945°E)** :

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "filter": [{
          "geo_distance": {
            "distance": "2km",
            "location": { "lat": 48.8584, "lon": 2.2945 }
          }
        }]
      }
    },
    "sort": [{
      "_geo_distance": {
        "location": { "lat": 48.8584, "lon": 2.2945 },
        "order": "asc", "unit": "km"
      }
    }],
    "_source": ["name", "location", "price", "rating"],
    "size": 10
  }' | python3 -m json.tool
```

**Exercice 4.1.1 — Rayon 5km, prix < 150 EUR** :

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "filter": [
          { "geo_distance": { "distance": "5km", "location": { "lat": 48.8584, "lon": 2.2945 } } },
          { "range": { "price": { "lt": 150 } } }
        ]
      }
    },
    "sort": [{ "_geo_distance": { "location": { "lat": 48.8584, "lon": 2.2945 }, "order": "asc", "unit": "km" } }],
    "_source": ["name", "price", "location"],
    "size": 10
  }'
```

---

### 4.2 - Recherche par bounding box

**Quartier Le Marais, Paris** :

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "filter": [{
          "geo_bounding_box": {
            "location": {
              "top_left": { "lat": 48.8650, "lon": 2.3500 },
              "bottom_right": { "lat": 48.8500, "lon": 2.3700 }
            }
          }
        }]
      }
    },
    "_source": ["name", "address.neighborhood", "price"],
    "size": 20
  }'
```

---

### 4.3 - Recherche par polygone

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "filter": [{
          "geo_polygon": {
            "location": {
              "points": [
                { "lat": 48.8600, "lon": 2.3500 },
                { "lat": 48.8650, "lon": 2.3600 },
                { "lat": 48.8550, "lon": 2.3650 },
                { "lat": 48.8500, "lon": 2.3550 }
              ]
            }
          }
        }]
      }
    },
    "size": 10
  }'
```

---

### 4.4 - Recherche combinee (geo + filtres metier)

**3km autour de Paris centre, prix 50-200 EUR, note >= 4.5, >= 2 chambres, Wifi** :

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "filter": [
          { "geo_distance": { "distance": "3km", "location": { "lat": 48.8566, "lon": 2.3522 } } },
          { "range": { "price": { "gte": 50, "lte": 200 } } },
          { "range": { "rating": { "gte": 4.5 } } },
          { "range": { "bedrooms": { "gte": 2 } } },
          { "term": { "amenities": "Wifi" } }
        ]
      }
    },
    "sort": [
      { "_geo_distance": { "location": { "lat": 48.8566, "lon": 2.3522 }, "order": "asc", "unit": "km" } },
      { "rating": "desc" }
    ],
    "size": 20
  }'
```

**Exercice 4.4.1 — New York, 5km, prix < 100 USD, superhost, instant bookable** :

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "bool": {
        "filter": [
          { "geo_distance": { "distance": "5km", "location": { "lat": 40.7128, "lon": -74.0060 } } },
          { "range": { "price": { "lt": 100 } } },
          { "term": { "host.host_is_superhost": true } },
          { "term": { "instant_bookable": true } }
        ]
      }
    },
    "sort": [{ "_geo_distance": { "location": { "lat": 40.7128, "lon": -74.0060 }, "order": "asc", "unit": "km" } }],
    "size": 20
  }'
```

---

### 4.5 - Recherche dans nested objects (reviews)

**Logements avec au moins une review rating = 5 en 2026** :

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "nested": {
        "path": "reviews",
        "query": {
          "bool": {
            "must": [
              { "term": { "reviews.rating": 5 } },
              { "range": { "reviews.date": { "gte": "2026-01-01", "lte": "2026-12-31" } } }
            ]
          }
        },
        "inner_hits": { "size": 3, "_source": ["reviews.reviewer_name", "reviews.rating", "reviews.comment"] }
      }
    },
    "size": 10
  }'
```

**Exercice 4.5.1 — Reviews contenant "amazing"** :

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "nested": {
        "path": "reviews",
        "query": {
          "match": { "reviews.comment": "amazing" }
        },
        "inner_hits": {
          "size": 3,
          "_source": ["reviews.reviewer_name", "reviews.comment"]
        }
      }
    },
    "size": 10
  }'
```

---

## Partie 5 : Agregations geospatiales

### 5.1 - Geohash Grid (heatmap)

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "heatmap": {
        "geohash_grid": { "field": "location", "precision": 5 },
        "aggs": {
          "avg_price": { "avg": { "field": "price" } },
          "centroid": { "geo_centroid": { "field": "location" } }
        }
      }
    }
  }' | python3 -m json.tool
```

**Precision geohash** :
- `1` : ~5000 km (continent)
- `5` : ~5 km (quartier)
- `7` : ~150 m (rue)
- `12` : ~1 cm (tres precis)

**Exercice 5.1.1 — Precision 7 (rues)** : remplacer `"precision": 5` par `"precision": 7`

---

### 5.2 - Geo Bounds (rectangle englobant d'une ville)

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": { "term": { "address.city": "Paris" } },
    "aggs": {
      "viewport": { "geo_bounds": { "field": "location" } }
    }
  }' | python3 -m json.tool
```

**Resultat** : retourne `top_left` et `bottom_right` pour centrer une carte.

---

### 5.3 - Prix moyen par quartier

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "neighborhoods": {
        "terms": { "field": "address.neighborhood", "size": 20, "order": { "avg_price": "desc" } },
        "aggs": {
          "avg_price": { "avg": { "field": "price" } },
          "avg_rating": { "avg": { "field": "rating" } },
          "count_superhosts": { "filter": { "term": { "host.host_is_superhost": true } } }
        }
      }
    }
  }' | python3 -m json.tool
```

**Exercice 5.3.1** : Trier par `avg_price` ascendant pour les quartiers les moins chers.

---

### 5.4 - Amenities les plus populaires

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "top_amenities": { "terms": { "field": "amenities", "size": 20 } }
    }
  }' | python3 -m json.tool
```

**Exercice 5.4.1 — Amenities pour prix > 200 EUR** :

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "query": { "range": { "price": { "gt": 200 } } },
    "aggs": {
      "top_amenities": { "terms": { "field": "amenities", "size": 20 } }
    }
  }'
```

---

### 5.5 - Histogram distribution des prix

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "size": 0,
    "aggs": {
      "price_distribution": {
        "histogram": { "field": "price", "interval": 50, "min_doc_count": 1 }
      }
    }
  }' | python3 -m json.tool
```

---

## Partie 6 : Optimisations avancees

### 6.1 - Monitoring slow logs

```bash
# Activer le slow log
curl -X PUT "localhost:9200/airbnb-listings/_settings" \
  -H "Content-Type: application/json" \
  -d '{
    "index.search.slowlog.threshold.query.warn": "1s",
    "index.search.slowlog.threshold.query.info": "500ms",
    "index.search.slowlog.threshold.query.debug": "200ms"
  }'

# Executer une requete lente
curl -s -X GET "localhost:9200/airbnb-listings/_search?size=10000" | python3 -m json.tool | grep took

# Voir les logs
docker exec chapitre-1-es01 tail -20 /usr/share/elasticsearch/logs/*_index_search_slowlog.log
```

### 6.2 - Script Painless (value score)

**Score = (rating × 10) / price** :

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "function_score": {
        "query": { "match_all": {} },
        "script_score": {
          "script": {
            "source": """
              double rating = doc[\"rating\"].size() > 0 ? doc[\"rating\"].value : 0;
              double price = doc[\"price\"].size() > 0 ? doc[\"price\"].value : 1;
              return rating * 10 / price;
            """
          }
        }
      }
    },
    "size": 10,
    "sort": ["_score"]
  }'
```

**Exercice 6.2.1 — Superhost bonus +20%** :

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "function_score": {
        "query": { "match_all": {} },
        "script_score": {
          "script": {
            "source": """
              double rating = doc[\"rating\"].size() > 0 ? doc[\"rating\"].value : 0;
              double price = doc[\"price\"].size() > 0 ? doc[\"price\"].value : 1;
              double base = rating * 10 / price;
              boolean superhost = doc[\"host.host_is_superhost\"].size() > 0 && doc[\"host.host_is_superhost\"].value;
              return superhost ? base * 1.2 : base;
            """
          }
        }
      }
    },
    "size": 10,
    "sort": ["_score"]
  }'
```

---

### 6.3 - Runtime fields (calcul dynamique)

**Disponibilite en pourcentage (availability_365 / 365 × 100)** :

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "runtime_mappings": {
      "availability_percent": {
        "type": "double",
        "script": { "source": "emit(doc[\"availability_365\"].value / 3.65)" }
      }
    },
    "query": { "range": { "availability_percent": { "gte": 50 } } },
    "fields": ["name", "availability_percent"],
    "size": 5
  }'
```

**Exercice 6.3.1 — price_per_person = price / accommodates** :

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "runtime_mappings": {
      "price_per_person": {
        "type": "double",
        "script": {
          "source": "int cap = doc[\"accommodates\"].size() > 0 ? doc[\"accommodates\"].value : 1; emit(doc[\"price\"].value / cap);"
        }
      }
    },
    "query": { "range": { "price_per_person": { "lte": 50 } } },
    "fields": ["name", "price", "accommodates", "price_per_person"],
    "size": 5
  }'
```

---

### 6.4 - ILM Policy (bonus production)

```bash
curl -X PUT "_ilm/policy/airbnb-policy" \
  -H "Content-Type: application/json" \
  -d '{
    "policy": {
      "phases": {
        "hot": {
          "actions": { "rollover": { "max_size": "50GB", "max_age": "30d" } }
        },
        "warm": {
          "min_age": "7d",
          "actions": { "forcemerge": { "max_num_segments": 1 } }
        },
        "delete": {
          "min_age": "90d",
          "actions": { "delete": {} }
        }
      }
    }
  }'
```

---

## Partie 7 : Cas d'usage business

### 7.1 - Dashboard statistiques hote

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": { "term": { "host.host_id": "67890" } },
    "size": 0,
    "aggs": {
      "total_listings": { "value_count": { "field": "listing_id" } },
      "avg_price": { "avg": { "field": "price" } },
      "avg_rating": { "avg": { "field": "rating" } },
      "total_reviews": { "sum": { "field": "number_of_reviews" } },
      "property_types": { "terms": { "field": "property_type" } }
    }
  }' | python3 -m json.tool
```

---

### 7.2 - Recherche de "deals" (rating eleve + prix bas)

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "function_score": {
        "query": {
          "bool": {
            "filter": [
              { "range": { "rating": { "gte": 4.5 } } },
              { "range": { "number_of_reviews": { "gte": 10 } } }
            ]
          }
        },
        "functions": [
          { "field_value_factor": { "field": "rating", "factor": 2, "modifier": "sqrt" } },
          { "script_score": { "script": { "source": "1 / (doc[\"price\"].value + 1)" } } }
        ],
        "score_mode": "multiply",
        "boost_mode": "replace"
      }
    },
    "size": 20,
    "sort": ["_score"]
  }'
```

---

### 7.3 - Recommandation "Similar listings"

```bash
curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "more_like_this": {
        "fields": ["name", "description", "address.neighborhood"],
        "like": [{ "_index": "airbnb-listings", "_id": "12345" }],
        "min_term_freq": 1,
        "max_query_terms": 12
      }
    },
    "size": 5
  }'
```

---

## Partie 8 : Visualisation Kibana

### 8.1 - Data View

1. **Menu (☰)** → **Management** → **Stack Management** → **Data Views**
2. **Create data view**
   - Name : `Airbnb Listings`
   - Index pattern : `airbnb-listings`
   - Timestamp : `created_at`
3. **Save**

### 8.2 - Discover

Filtres KQL :
```
address.city: "Paris" AND price < 150
rating >= 4.5 AND host.host_is_superhost: true
```

### 8.3 - Carte geographique (Maps)

1. **Menu** → **Maps** → **Create map**
2. **Add layer** → **Documents**
   - Index : `airbnb-listings`
   - Geospatial field : `location`
3. **Style** : Color by `price`, Size by `rating`
4. **Save**

### 8.4 - Dashboard

6 visualisations a assembler :

| # | Type | Configuration |
|---|------|--------------|
| 1 | Map | location, color by price |
| 2 | Bar chart | Top 10 villes (`address.city`) |
| 3 | Histogram | Distribution prix (interval: 50) |
| 4 | Pie chart | Prix moyen par `property_type` |
| 5 | Metric | Superhosts vs reguliers |
| 6 | Tag cloud | Top 20 `amenities` |

---

## Partie 9 : Tests de performance

### 9.1 - Benchmark geo_distance

```bash
# Test 1 : geo_distance simple
time curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{"query": {"geo_distance": {"distance": "5km", "location": {"lat": 48.8566, "lon": 2.3522}}}, "size": 100}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Resultats: {d[\"hits\"][\"total\"][\"value\"]}, Temps: {d[\"took\"]}ms')"

# Test 2 : geo_distance + filtres complexes
time curl -s -X POST "localhost:9200/airbnb-listings/_search" \
  -H "Content-Type: application/json" \
  -d '{"query": {"bool": {"filter": [{"geo_distance": {"distance": "5km", "location": {"lat": 48.8566, "lon": 2.3522}}}, {"range": {"price": {"lte": 150}}}, {"range": {"rating": {"gte": 4.0}}}, {"term": {"instant_bookable": true}}]}}, "size": 100}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Resultats: {d[\"hits\"][\"total\"][\"value\"]}, Temps: {d[\"took\"]}ms')"
```

### 9.2 - Impact du forcemerge

```bash
# Avant forcemerge
curl -s "localhost:9200/airbnb-listings/_stats/segments" | python3 -m json.tool | grep -E '"count"|"memory"'

# Apres forcemerge
curl -X POST "localhost:9200/airbnb-listings/_forcemerge?max_num_segments=1"

# Re-tester la meme requete et comparer le temps
```

**Resultat attendu** : gain de 10-30% apres forcemerge.

---

## Troubleshooting

| Probleme | Cause | Solution |
|---------|-------|----------|
| geo_distance ne retourne rien | Coordonnees inversees | Verifier `{ "lat": ..., "lon": ... }` (lat AVANT lon) |
| Nested query ne fonctionne pas | Champ pas type `nested` | Recrer l'index avec le bon mapping |
| Requetes lentes malgre forcemerge | `size` trop grand | Reduire `size` ou utiliser pagination |
| count = 0 apres bulk | Format NDJSON incorrect | Utiliser `--data-binary` avec `-H "Content-Type: application/x-ndjson"` |
| Slow log vide | Threshold trop haut | Baisser `threshold.query.info` a `100ms` |

---

## Livrables

- [ ] Index `airbnb-listings` avec 50k+ documents
- [ ] Mapping geospatial correct (`geo_point`, `nested`)
- [ ] 10 requetes geospatiales fonctionnelles
- [ ] 5 agregations geospatiales avec resultats
- [ ] Dashboard Kibana avec carte interactive
- [ ] Script Painless personnalise
- [ ] Analyse performance (avant/apres forcemerge)
