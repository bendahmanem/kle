# SPEC.md — KLE (Kit Labo Elastic)

Correction du TP1 ELK — Mise en place d'un environnement Elastic Stack 9.4.2.

## Structure

```
kle/
├── SPEC.md
├── README.md
├── TP1-correction.md          # Corrige detaille du TP1
├── docker-compose.yml         # Stack ELK complet
├── scripts/
│   ├── check-docker.sh        # Verif Docker installe
│   ├── check-sys.sh           # Verif vm.max_map_count
│   ├── check-cluster.sh       # Sante cluster ES
│   ├── create-index.sh        # Creation index sample
│   └── index-document.sh      # Indexer un document
└── .env                        # Variables environment
```

## Stack ELK

- **Elasticsearch** (single node, no security for dev)
- **Kibana** (port 5601)
- **Logstash** (optionnel, port 5044)
- Beats optional

## Versions

- Elasticsearch: 9.4.2
- Kibana: 9.4.2
- Docker Compose v2