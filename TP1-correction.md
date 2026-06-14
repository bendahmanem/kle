# TP1 - Correction : Mise en place d'un environnement Elastic Stack

> **Module ELK - Chapitre 1** | Version Elastic : 9.4.2 | Duree : 2-3h

---

## Preparation

### Avant de commencer

```bash
# 1. Verifier Docker
./scripts/check-docker.sh

# 2. Verifier vm.max_map_count (Linux uniquement)
./scripts/check-sys.sh
```

---

## Partie 1 : Configuration systeme

### Etape 1.1 : vm.max_map_count

**Sur Linux :**

```bash
# Verifier la valeur actuelle
sysctl vm.max_map_count
# Output attendu : vm.max_map_count = 262144

# Si inferieur a 262144, appliquer :
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

**Sur macOS (Docker Desktop) :** pas d'action requise — Docker Desktop configure automatiquement.

**Sur Windows (WSL2) :** modifier `C:\Users\<USER>\.wslconfig` puis `wsl --shutdown`.

---

## Partie 2 : Deploiement du Stack

### Etape 2.1 : Lancer le stack

```bash
# Se placer dans le repertoire du projet
cd kle

# Lancer les conteneurs
docker-compose up -d

# Verifier le statut
docker-compose ps
```

**Sortie attendue :**
```
NAME                    SERVICE   STATUS    PORTS
chapitre-1-es01-1       es01      running  0.0.0.0:9200->9200/tcp
chapitre-1-kibana-1     kibana    running  0.0.0.0:5601->5601/tcp
```

### Etape 2.2 : Attendre que les services soient prets

```bash
# Suivre les logs (Ctrl+C pour quitter)
docker-compose logs -f

# Attendre ces messages :
# es01      : "started"
# kibana    : "http server running at http://0.0.0.0:5601"
```

**Temps moyen de demarrage :** 30-60 secondes. Patience.

---

## Partie 3 : Verification et exploration

### Etape 3.1 : Sante du cluster

```bash
# Sante globale
curl -X GET "localhost:9200/_cat/health?v&pretty"

# Reponse attendue :
# epoch    timestamp  cluster          status  node.total node.data  shards  pri  repo  segment_memory  segments  successful_segments
# xxxxxxx  2024-xx    kle-cluster     green   1         1         0      0              0b          0        0
```

**Statut vert = operationnel.** Si jaune, c'est normal en single-node.

### Etape 3.2 : Info cluster

```bash
curl -X GET "localhost:9200/_cluster/stats?pretty"
```

### Etape 3.3 : Creer un index

```bash
# Methode 1 : avec le script fourni
./scripts/create-index.sh students

# Methode 2 : curl direct
curl -X PUT "localhost:9200/students" \
  -H "Content-Type: application/json" \
  -d '{
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0
    },
    "mappings": {
      "properties": {
        "name": { "type": "text" },
        "email": { "type": "keyword" },
        "age": { "type": "integer" }
      }
    }
  }'
```

### Etape 3.4 : Indexer des documents

```bash
# Methode 1 : avec le script fourni
./scripts/index-document.sh students

# Methode 2 : curl direct
curl -X POST "localhost:9200/students/_doc/1" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Martin", "email": "alice@isitech.fr", "age": 21}'

curl -X POST "localhost:9200/students/_doc/2" \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Dupont", "email": "bob@isitech.fr", "age": 22}'
```

### Etape 3.5 : Rechercher dans Dev Tools (Kibana)

Ouvrir Kibana : **http://localhost:5601**

Aller dans **Dev Tools** (icone chronometre en bas a gauche) :

```json
// Lister tous les documents
GET students/_search

// Filtrer par promo
GET students/_search
{
  "query": {
    "term": { "promo": "B2" }
  }
}

// Compter les documents
GET students/_count

// Recherche textuelle
GET students/_search
{
  "query": {
    "match": { "name": "Alice" }
  }
}
```

---

## Partie 4 : Exploration Kibana

### Acces

- URL : **http://localhost:5601**
- Premier lancement : selectionner "Explore on my own"

### Discover

1. **Create index pattern** : `students`
2. **Time field** : `created_at` (ou `@timestamp`)
3. Cliquer **Discover** pour explorer les donnees

### Visualizations possibles

- **Bar chart** : nombre d'etudiants par promo
- **Metric** : age moyen, age max/min
- **Data table** : liste des etudiants avec filtres

---

## Commandes utiles

```bash
# Arreter le stack
docker-compose down

# Arreter + supprimer les donnees
docker-compose down -v

# Redemarrer
docker-compose restart

# Voir les logs d'un service
docker-compose logs -f es01
docker-compose logs -f kibana

# Executer des requetes ES
curl -X GET "localhost:9200/_cat/indices?v"

# Supprimer un index
curl -X DELETE "localhost:9200/students"
```

---

## Problemes courants

| Probleme | Solution |
|---------|----------|
| `vm.max_map_count` trop bas | `sudo sysctl -w vm.max_map_count=262144` |
| Elasticsearch ne demarre pas | `docker-compose logs es01` — souvent memoire insuffisante |
| Kibana ne se connecte pas a ES | Attendre 30s le temps qu'ES soit pret |
| Port 9200 deja utilise | `docker-compose down` puis `docker-compose up -d` |
| Verticaux en permanence | Ajouter `vm.max_map_count=262144` dans `/etc/sysctl.conf` |

---

## Resume des commandes a retenir

```bash
# Demarrage
docker-compose up -d

# Verification sante
curl localhost:9200/_cat/health?v

# Verification cluster
curl localhost:9200/_cluster/stats?pretty

# Creation index
curl -X PUT localhost:9200/monindex -H "Content-Type: application/json" -d '{...}'

# Indexer document
curl -X POST localhost:9200/monindex/_doc/1 -H "Content-Type: application/json" -d '{...}'

# Rechercher
curl -X GET localhost:9200/monindex/_search -H "Content-Type: application/json" -d '{"query": {...}}'
```