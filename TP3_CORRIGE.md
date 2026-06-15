# TP3 - Corrections et Réponses
## Recherche géospatiale Airbnb avec optimisations avancées
### ELK Stack 9.4.2

---

## Préparation

### Démarrer la stack
```bash
cd docker
docker-compose up -d
# Attendre ~2 min que ES soit prêt
docker exec es01 curl -s http://localhost:9200/_cluster/health | jq
```

### Générer le dataset
```bash
cd scripts
pip install pandas requests faker
python3 tp3-airbnb-dataset.py --index
```

---

## Partie 1 : Dataset

**Script** : `scripts/tp3-airbnb-dataset.py` — génère 50 000 listings (10 000 par ville) et les indexe.

```bash
# Générer uniquement (sans indexer)
python3 tp3-airbnb-dataset.py

# Générer + indexer
python3 tp3-airbnb-dataset.py --index

# Générer moins de documents pour tester
python3 tp3-airbnb-dataset.py --index --count 5000
```

---

## Partie 2 : Mapping

### 2.1 - Supprimer l'index
```bash
curl -X DELETE "localhost:9200/airbnb-listings"
```

### 2.2 - Créer l'index (exécuter dans Dev Tools Kibana)
```json
PUT /airbnb-listings
{
  "settings": {
    "number_of_shards": 2,
    "number_of_replicas": 0,
    "refresh_interval": "30s",
    "max_result_window": 50000,
    "analysis": {
      "analyzer": {
        "address_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "asciifolding"]
        }
      }
    }
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
          "street": { "type": "text", "analyzer": "address_analyzer" },
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
}
```

### 2.3 - Vérifier le mapping
```bash
GET /airbnb-listings/_mapping
```

### 2.4 - Tester le geo_point
```json
POST /airbnb-listings/_doc/test
{
  "listing_id": "test",
  "name": "Test listing",
  "location": { "lat": 48.8566, "lon": 2.3522 },
  "price": 100,
  "rating": 4.5
}
```

```json
GET /airbnb-listings/_search
{
  "query": {
    "geo_distance": {
      "distance": "1km",
      "location": { "lat": 48.8566, "lon": 2.3522 }
    }
  }
}
```
→ Le document `test` doit apparaître ✅

---

## Partie 3 : Indexation

### 3.1 - Avec le script
```bash
python3 tp3-airbnb-dataset.py --index
```

### 3.2 - Vérifier
```bash
GET /airbnb-listings/_count
```
→ `{"count": 50000}`

### 3.3 - Optimisations post-indexation
```json
PUT /airbnb-listings/_settings
{ "index.refresh_interval": "1s" }

POST /airbnb-listings/_forcemerge?max_num_segments=1

POST /airbnb-listings/_refresh
```

### 3.4 - Statistiques
```bash
GET /airbnb-listings/_stats?human
```

---

## Partie 4 : Recherches géospatiales

### 4.1 - Recherche par distance (Tour Eiffel, 2km)
```json
GET /airbnb-listings/_search
{
  "query": {
    "bool": {
      "filter": [
        {
          "geo_distance": {
            "distance": "2km",
            "location": { "lat": 48.8584, "lon": 2.2945 }
          }
        }
      ]
    }
  },
  "size": 10,
  "sort": [
    {
      "_geo_distance": {
        "location": { "lat": 48.8584, "lon": 2.2945 },
        "order": "asc",
        "unit": "km"
      }
    }
  ],
  "_source": ["name", "location", "price", "rating"],
  "script_fields": {
    "distance_km": {
      "script": {
        "source": "doc['location'].arcDistance(params.lat, params.lon) / 1000",
        "params": { "lat": 48.8584, "lon": 2.2945 }
      }
    }
  }
}
```

**Exercice 4.1.1** — Rayon 5km, price < 150 :
```json
GET /airbnb-listings/_search
{
  "query": {
    "bool": {
      "filter": [
        { "geo_distance": { "distance": "5km", "location": { "lat": 48.8584, "lon": 2.2945 } } },
        { "range": { "price": { "lt": 150 } } }
      ]
    }
  },
  "size": 10,
  "sort": [{ "_geo_distance": { "location": { "lat": 48.8584, "lon": 2.2945 }, "order": "asc", "unit": "km" } }]
}
```

### 4.2 - Recherche par bounding box (Le Marais)
```json
GET /airbnb-listings/_search
{
  "query": {
    "bool": {
      "filter": [
        {
          "geo_bounding_box": {
            "location": {
              "top_left": { "lat": 48.8650, "lon": 2.3500 },
              "bottom_right": { "lat": 48.8500, "lon": 2.3700 }
            }
          }
        }
      ]
    }
  },
  "size": 20
}
```

**Exercice 4.2.1** — Votre ville, definez le bounding box :
```json
// Exemple pour New York (Manhattan)
GET /airbnb-listings/_search
{
  "query": {
    "bool": {
      "filter": [
        {
          "geo_bounding_box": {
            "location": {
              "top_left": { "lat": 40.8200, "lon": -74.0200 },
              "bottom_right": { "lat": 40.7000, "lon": -73.9300 }
            }
          }
        }
      ]
    }
  },
  "size": 10
}
```

### 4.3 - Recherche par polygone
```json
GET /airbnb-listings/_search
{
  "query": {
    "bool": {
      "filter": [
        {
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
        }
      ]
    }
  }
}
```

### 4.4 - Filtres combinés (Paris, 3km, 50-200€, rating ≥ 4.5, ≥ 2 chambres, Wifi)
```json
GET /airbnb-listings/_search
{
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
}
```

**Exercice 4.4.1** — New York, 5km, < 100 USD, Superhost, instant bookable :
```json
GET /airbnb-listings/_search
{
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
}
```

### 4.5 - Nested query (reviews avec rating = 5 en 2026)
```json
GET /airbnb-listings/_search
{
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
      "inner_hits": {
        "size": 3,
        "_source": ["reviews.reviewer_name", "reviews.rating", "reviews.comment"]
      }
    }
  },
  "size": 10
}
```

**Exercice 4.5.1** — Reviews contenant "amazing" :
```json
GET /airbnb-listings/_search
{
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
}
```

---

## Partie 5 : Agrégations

### 5.1 - Heatmap geohash_grid (precision 5)
```json
GET /airbnb-listings/_search
{
  "size": 0,
  "aggs": {
    "heatmap": {
      "geohash_grid": {
        "field": "location",
        "precision": 5
      },
      "aggs": {
        "avg_price": { "avg": { "field": "price" } },
        "centroid": { "geo_centroid": { "field": "location" } }
      }
    }
  }
}
```

**Exercice 5.1.1** — Precision 7 (niveau rue) :
```json
GET /airbnb-listings/_search
{
  "size": 0,
  "aggs": {
    "heatmap": {
      "geohash_grid": {
        "field": "location",
        "precision": 7
      }
    }
  }
}
```

### 5.2 - Geo Bounds (rectangle englobant Paris)
```json
GET /airbnb-listings/_search
{
  "size": 0,
  "query": { "term": { "address.city": "Paris" } },
  "aggs": {
    "viewport": { "geo_bounds": { "field": "location" } }
  }
}
```

### 5.3 - Prix moyen par quartier (trié par prix desc)
```json
GET /airbnb-listings/_search
{
  "size": 0,
  "aggs": {
    "neighborhoods": {
      "terms": {
        "field": "address.neighborhood",
        "size": 20,
        "order": { "avg_price": "desc" }
      },
      "aggs": {
        "avg_price": { "avg": { "field": "price" } },
        "avg_rating": { "avg": { "field": "rating" } },
        "count_superhosts": { "filter": { "term": { "host.host_is_superhost": true } } }
      }
    }
  }
}
```

**Exercice 5.3.1** — Top 5 + Bottom 5 quartiers :
```json
// Top 5 les plus chers
GET /airbnb-listings/_search
{
  "size": 0,
  "aggs": {
    "neighborhoods": {
      "terms": { "field": "address.neighborhood", "size": 5, "order": { "avg_price": "desc" } },
      "aggs": { "avg_price": { "avg": { "field": "price" } } }
    }
  }
}

// Bottom 5 les moins chers
GET /airbnb-listings/_search
{
  "size": 0,
  "aggs": {
    "neighborhoods": {
      "terms": { "field": "address.neighborhood", "size": 5, "order": { "avg_price": "asc" } },
      "aggs": { "avg_price": { "avg": { "field": "price" } } }
    }
  }
}
```

### 5.4 - Top 20 amenities
```json
GET /airbnb-listings/_search
{
  "size": 0,
  "aggs": {
    "top_amenities": {
      "terms": { "field": "amenities", "size": 20 }
    }
  }
}
```

**Exercice 5.4.1** — Amenities pour price > 200 :
```json
GET /airbnb-listings/_search
{
  "size": 0,
  "query": { "range": { "price": { "gt": 200 } } },
  "aggs": {
    "top_amenities": { "terms": { "field": "amenities", "size": 20 } }
  }
}
```

### 5.5 - Histogram distribution des prix (interval 50)
```json
GET /airbnb-listings/_search
{
  "size": 0,
  "aggs": {
    "price_distribution": {
      "histogram": {
        "field": "price",
        "interval": 50,
        "min_doc_count": 1
      }
    }
  }
}
```

---

## Partie 6 : Optimisations

### 6.1 - Slow log + requête lente
```json
PUT /airbnb-listings/_settings
{
  "index.search.slowlog.threshold.query.warn": "1s",
  "index.search.slowlog.threshold.query.info": "500ms",
  "index.search.slowlog.threshold.query.debug": "200ms"
}
```

```json
GET /airbnb-listings/_search
{
  "query": { "match_all": {} },
  "size": 10000
}
```

```bash
docker exec es01 tail -f /usr/share/elasticsearch/logs/docker-cluster_index_search_slowlog.log
```

**Exercice 6.1.1** — Analyser une requête lente avec `_explain` :
```json
GET /airbnb-listings/_explain/<listing_id>
{
  "query": { "match_all": {} }
}
```

### 6.2 - Script Painless (value score = rating×10/price)
```json
GET /airbnb-listings/_search
{
  "query": {
    "function_score": {
      "query": { "match_all": {} },
      "script_score": {
        "script": {
          "source": """
            double rating = doc['rating'].size() > 0 ? doc['rating'].value : 0;
            double price = doc['price'].size() > 0 ? doc['price'].value : 1;
            return rating * 10 / price;
          """
        }
      }
    }
  },
  "size": 10,
  "sort": [{ "_score": "desc" }]
}
```

**Exercice 6.2.1** — Superhost bonus +20% :
```json
GET /airbnb-listings/_search
{
  "query": {
    "function_score": {
      "query": { "match_all": {} },
      "script_score": {
        "script": {
          "source": """
            double rating = doc['rating'].size() > 0 ? doc['rating'].value : 0;
            double price = doc['price'].size() > 0 ? doc['price'].value : 1;
            double baseScore = rating * 10 / price;
            boolean isSuperhost = doc['host.host_is_superhost'].size() > 0 && doc['host.host_is_superhost'].value;
            return isSuperhost ? baseScore * 1.2 : baseScore;
          """
        }
      }
    }
  },
  "size": 10,
  "sort": [{ "_score": "desc" }]
}
```

### 6.3 - Runtime field (availability_percent)
```json
GET /airbnb-listings/_search
{
  "runtime_mappings": {
    "availability_percent": {
      "type": "double",
      "script": {
        "source": "emit(doc['availability_365'].value / 3.65)"
      }
    }
  },
  "query": { "range": { "availability_percent": { "gte": 50 } } },
  "fields": ["name", "availability_percent"],
  "_source": false,
  "size": 10
}
```

**Exercice 6.3.1** — Runtime field `price_per_person` :
```json
GET /airbnb-listings/_search
{
  "runtime_mappings": {
    "price_per_person": {
      "type": "double",
      "script": {
        "source": "emit(doc['price'].value / doc['accommodates'].value)"
      }
    }
  },
  "query": { "range": { "price_per_person": { "lte": 50 } } },
  "fields": ["name", "price", "accommodates", "price_per_person"],
  "size": 10
}
```

### 6.4 - ILM Policy (bonus)
```json
PUT _ilm/policy/airbnb-policy
{
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
}
```

---

## Partie 7 : Cas business

### 7.1 - Dashboard stats hôte
```json
GET /airbnb-listings/_search
{
  "query": { "term": { "host.host_id": "67890" } },
  "size": 0,
  "aggs": {
    "total_listings": { "value_count": { "field": "listing_id" } },
    "avg_price": { "avg": { "field": "price" } },
    "avg_rating": { "avg": { "field": "rating" } },
    "total_reviews": { "sum": { "field": "number_of_reviews" } },
    "property_types": { "terms": { "field": "property_type" } }
  }
}
```

### 7.2 - Recherche de "deals" (rating ≥ 4.5, ≥ 10 reviews)
```json
GET /airbnb-listings/_search
{
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
        { "script_score": { "script": { "source": "1 / (doc['price'].value + 1)" } } }
      ],
      "score_mode": "multiply",
      "boost_mode": "replace"
    }
  },
  "size": 20,
  "sort": [{ "_score": "desc" }]
}
```

### 7.3 - Similar listings (More Like This)
```json
GET /airbnb-listings/_search
{
  "query": {
    "more_like_this": {
      "fields": ["name", "description", "address.neighborhood"],
      "like": [{ "_index": "airbnb-listings", "_id": "12345" }],
      "min_term_freq": 1,
      "max_query_terms": 12
    }
  },
  "size": 5
}
```

---

## Partie 8 : Kibana

### 8.1 - Data View
1. **Stack Management** → **Data Views**
2. **Create data view**
   - Name: `Airbnb Listings`
   - Index pattern: `airbnb-listings`
   - Timestamp field: `created_at`
3. **Save**

### 8.2 - Discover requêtes KQL
```
address.city: "Paris" AND price < 150
rating >= 4.5 AND host.host_is_superhost: true
```

### 8.3 - Carte Maps
1. **Maps** → **Add layer** → **Documents**
2. Index: `airbnb-listings`, Geospatial field: `location`
3. Style → Color by: `price`, Size by: `rating`

### 8.4 - Dashboard (6 visualisations)
1. **Maps** (carte géographique créée en 8.3)
2. **Bar chart** — Top 10 villes par nombre de listings
   - X-axis: Terms `address.city`
   - Y-axis: Count
3. **Histogram** — Distribution des prix (interval: 50)
4. **Pie chart** — Prix moyen par type de logement
   - Slice by: Terms `property_type`
   - Metric: Average `price`
5. **Metric** — Superhosts vs réguliers
   - Filters: `host.host_is_superhost: true` et `host.host_is_superhost: false`
6. **Tag cloud** — Top 20 amenities
   - Tags: Terms `amenities` (size: 20)

Assembler dans un dashboard avec filtres globaux (city, price range, rating).

---

## Partie 9 : Performance

### 9.1 - Benchmark
```bash
# Test 1 : geo_distance simple
time curl -s -X GET "localhost:9200/airbnb-listings/_search" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"geo_distance":{"distance":"5km","location":{"lat":48.8566,"lon":2.3522}}},"size":100}'

# Test 2 : geo_distance + filtres complexes
time curl -s -X GET "localhost:9200/airbnb-listings/_search" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"bool":{"filter":[{"geo_distance":{"distance":"5km","location":{"lat":48.8566,"lon":2.3522}}},{"range":{"price":{"lte":150}}},{"range":{"rating":{"gte":4.0}}},{"term":{"instant_bookable":true}}]}},"size":100}'
```

### 9.2 - Avant/Après forcemerge
```bash
# Statistiques segments avant
GET /airbnb-listings/_stats/segments

# Forcemerge
POST /airbnb-listings/_forcemerge?max_num_segments=1

# Statistiques après
GET /airbnb-listings/_stats/segments
```

---

## Troubleshooting

| Problème | Cause | Solution |
|----------|-------|----------|
| geo_distance ne retourne rien | Coordonnées inversées | Vérifier `{ "lat": 48.8566, "lon": 2.3522 }` (lat avant lon) |
| Nested query ne fonctionne pas | Type pas `nested` | Recréer l'index avec le bon mapping |
| Requêtes lentes | Trop de segments | `POST /airbnb-listings/_forcemerge?max_num_segments=1` |
| Slow log vide | Threshold trop haut | Baisser `query.warn` à `500ms` |

---

## Commandes utiles de vérification

```bash
# Santé du cluster
GET _cluster/health

# Statut de l'index
GET /airbnb-listings/_stats

# Nombre de documents
GET /airbnb-listings/_count

# Mapping complet
GET /airbnb-listings/_mapping

# Segments
GET /airbnb-listings/_segments

# Requêtes actives
GET /_nodes/stats/indices/search
```