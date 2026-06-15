# SPEC.md — KLE (Kit Labo Elastic)

Corriges TP1 et TP3 ELK — Elastic Stack 9.4.2.

## Structure

```
kle/
├── SPEC.md
├── README.md
├── TP1-correction.md          # TP1 : Mise en place ELK
├── TP3-correction.md          # TP3 : Recherche geospatiale Airbnb
├── docker-compose.yml         # Stack ELK (ES + Kibana)
├── scripts/
│   ├── check-docker.sh
│   ├── check-sys.sh
│   ├── check-cluster.sh
│   ├── create-index.sh
│   ├── index-document.sh
│   └── tp3-airbnb-dataset.py  # Generation 50k+ listings
└── logstash/
    └── pipeline/logstash.conf
```

## TPs couverts

### TP1 — Mise en place Elastic Stack
- docker-compose ES 9.4.2 + Kibana
- vm.max_map_count, Docker
- Index creation, bulk indexing
- Recherches (match, term, range, bool)
- Kibana Discover + Data Views
- CRUD management
- Logstash bonus

### TP3 — Recherche geospatiale Airbnb
- Script Python dataset (Paris, NY, Londres, Barcelona, Amsterdam)
- Mapping : geo_point, nested, keyword arrays
- Recherches : geo_distance, geo_bounding_box, geo_polygon
- Nested queries (reviews)
- Agregations : geohash_grid, geo_bounds, geo_centroid, terms, histogram
- Optimisations : slow logs, Painless scripts, runtime fields, ILM
- Business cases : host stats, deals, similar listings
- Kibana Maps + Dashboard
- Benchmark avant/apres forcemerge

## Stack

- Elasticsearch 9.4.2 (single-node, no security)
- Kibana 9.4.2
- Logstash 9.4.2 (optionnel, commented out)