# KLE — Kit Labo Elastic

Corrige du TP1 ELK : Mise en place d'un environnement Elastic Stack 9.4.2.

## Contenu

```
kle/
├── TP1-correction.md          # Corrige detaille du TP1
├── docker-compose.yml         # Stack ELK complet (ES + Kibana)
├── scripts/
│   ├── check-docker.sh        # Verif Docker installe
│   ├── check-sys.sh           # Verif vm.max_map_count
│   ├── check-cluster.sh       # Sante cluster ES
│   ├── create-index.sh        # Creation index avec mapping
│   └── index-document.sh      # Indexation + recherches
└── README.md
```

## Stack ELK deploye

| Service | Port | Description |
|---------|------|-------------|
| Elasticsearch | 9200 | Moteur de recherche et stockage |
| Kibana | 5601 | Interface web d'exploration |

## Demarrage rapide

```bash
# 1. Cloner ce repo
git clone https://github.com/bendahmanem/kle.git
cd kle

# 2. Verifier Docker
./scripts/check-docker.sh

# 3. Lancer le stack
docker-compose up -d

# 4. Attendre ~30s puis verifier
./scripts/check-cluster.sh
```

## Services

- **Elasticsearch** : http://localhost:9200
- **Kibana** : http://localhost:5601

## Scripts

| Script | Role |
|--------|------|
| `check-docker.sh` | Verifie Docker + Docker Compose |
| `check-sys.sh` | Verifie/configure vm.max_map_count |
| `check-cluster.sh` | Affiche sante, nodes, indices |
| `create-index.sh` | Cree l'index `students` |
| `index-document.sh` | Indexe 3 documents + 2 recherches |

## Arret

```bash
docker-compose down        # Arrete les conteneurs
docker-compose down -v     # Arrete + supprime les donnees
```