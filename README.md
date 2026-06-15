# KLE — Kit Labo Elastic

Corriges des TPs ELK : Mise en place d'un environnement Elastic Stack 9.4.2.

## TPs disponibles

| TP | Sujet | Duree |
|----|-------|-------|
| TP1 | Mise en place Elastic Stack + base ES | 2-3h |
| TP2 | Recherche geospatiale Airbnb + optimisations | 3-4h |

## Contenu par TP

### TP1-correction.md
- Installation Docker + vm.max_map_count
- Deploiement ES + Kibana (docker-compose)
- Creation d'index, mapping, bulk indexing
- Recherches full-text, filtres, bool queries
- Kibana Discover + Data Views
- CRUD (update, delete, close/open index)
- Logstash bonus
- Troubleshooting + validation

### TP3-correction.md
- Script Python de generation dataset (50k+ listings multi-villes)
- Mapping geospatial (`geo_point`, `nested`, `geo_shape`)
- Recherches : `geo_distance`, `geo_bounding_box`, `geo_polygon`
- Nested queries sur reviews
- Agregations : `geohash_grid`, `geo_bounds`, `geo_centroid`, terms, histogram
- Optimisations : slow logs, Painless scripts, runtime fields, ILM
- Business cases : host stats, deals scoring, similar listings
- Kibana Maps + Dashboard
- Benchmark et impact forcemerge

## Demarrage rapide

```bash
# Lancer la stack
docker-compose up -d

# Verifier ES
./scripts/check-cluster.sh

# Generer le dataset (TP3)
pip install faker pandas requests
python3 scripts/tp3-airbnb-dataset.py --count 50000
```

## Services

- **Elasticsearch** : http://localhost:9200
- **Kibana** : http://localhost:5601

## Scripts

| Script | Role |
|--------|------|
| `check-docker.sh` | Verifie Docker installe |
| `check-sys.sh` | Configure vm.max_map_count |
| `check-cluster.sh` | Sante cluster + nodes + indices |
| `create-index.sh` | Cree index students (TP1) |
| `index-document.sh` | Indexe 3 docs + recherches (TP1) |
| `tp3-airbnb-dataset.py` | Genere 50k+ listings Airbnb (TP3) |

## Arret

```bash
docker-compose down        # Arrete
docker-compose down -v    # Arrete + supprime les donnees
```