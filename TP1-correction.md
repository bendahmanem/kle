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
---

## Partie 4 : Creer et manipuler un index

### Etape 4.1 : Creer un index avec mapping explicite

**Via curl :**

```bash
curl -X PUT "localhost:9200/products" -H "Content-Type: application/json" -d'
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "name": {
        "type": "text",
        "fields": { "keyword": { "type": "keyword" } }
      },
      "description": { "type": "text" },
      "price": { "type": "float" },
      "in_stock": { "type": "boolean" },
      "category": { "type": "keyword" },
      "tags": { "type": "keyword" },
      "created_at": { "type": "date" }
    }
  }
}'
```

**Via Kibana Dev Tools (recommande) :**

1. Menu (☰) → Management → Dev Tools
2. Saisir la requete :
```json
PUT /products
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "name": {
        "type": "text",
        "fields": { "keyword": { "type": "keyword" } }
      },
      "description": { "type": "text" },
      "price": { "type": "float" },
      "in_stock": { "type": "boolean" },
      "category": { "type": "keyword" },
      "tags": { "type": "keyword" },
      "created_at": { "type": "date" }
    }
  }
}
```
3. Executer avec ▶ ou `Ctrl+Enter`

**Reponse attendue :**
```json
{
  "acknowledged": true,
  "shards_acknowledged": true,
  "index": "products"
}
```

### Etape 4.2 : Verifier la creation de l'index

```bash
curl -X GET "localhost:9200/_cat/indices?v"
```

**Sortie attendue :**
```
health status index    uuid    pri rep docs.count docs.deleted store.size pri.store.size
yellow open   products AbC123  1   0   0          0            225b       225b
```

> **Note :** `yellow` est normal avec 0 replicas sur un single-node.

### Etape 4.3 : Consulter le mapping

```bash
GET /products/_mapping
```

Verifier que tous les champs sont definis avec les types corrects.

---

## Partie 5 : Indexer des documents

### Etape 5.1 : Indexer un document (ID auto-genere)

```bash
POST /products/_doc
{
  "name": "Laptop Dell XPS 15",
  "description": "Powerful laptop with 16GB RAM and 512GB SSD",
  "price": 1299.99,
  "in_stock": true,
  "category": "Electronics",
  "tags": ["laptop", "dell", "xps"],
  "created_at": "2026-06-14T10:00:00"
}
```

**Reponse :**
```json
{
  "_index": "products",
  "_id": "AbC123...",
  "_version": 1,
  "result": "created",
  "_shards": { "total": 1, "successful": 1, "failed": 0 }
}
```

### Etape 5.2 : Indexer un document (ID specifique)

```bash
POST /products/_doc/prod-001
{
  "name": "Laptop Dell XPS 15",
  "description": "Powerful laptop with 16GB RAM and 512GB SSD",
  "price": 1299.99,
  "in_stock": true,
  "category": "Electronics",
  "tags": ["laptop", "dell", "xps"],
  "created_at": "2026-06-14T10:00:00"
}
```

### Etape 5.3 : Indexer plusieurs documents (bulk)

```bash
POST /products/_bulk
{ "index": { "_id": "prod-002" } }
{ "name": "Samsung Galaxy S24", "description": "Smartphone with 8GB RAM", "price": 899.99, "in_stock": true, "category": "Electronics", "tags": ["phone", "samsung"], "created_at": "2026-06-14T11:00:00" }
{ "index": { "_id": "prod-003" } }
{ "name": "Logitech MX Master 3", "description": "Wireless mouse ergonomic", "price": 99.99, "in_stock": false, "category": "Accessories", "tags": ["mouse", "logitech"], "created_at": "2026-06-14T12:00:00" }
```

### Etape 5.4 : Rechercher dans l'index

**Tous les documents :**
```bash
GET /products/_search
```

**Filtrer par categorie :**
```bash
GET /products/_search
{
  "query": {
    "term": { "category": "Electronics" }
  }
}
```

**Recherche textuelle (champ `name`) :**
```bash
GET /products/_search
{
  "query": {
    "match": { "name": "laptop" }
  }
}
```

**Filtrer par prix :**
```bash
GET /products/_search
{
  "query": {
    "range": { "price": { "gte": 100, "lte": 1000 } }
  }
}
```

**Filtrer produits en stock :**
```bash
GET /products/_search
{
  "query": {
    "term": { "in_stock": true }
  }
}
```

---

## Acces Kibana

- URL : **http://localhost:5601**
- Menu (☰) → **Management** → **Dev Tools** pour les requetes JSON
- Menu (☰) → **Discover** pour explorer visuellement les donnees indexees

### Si token d'enrollment requis (Elasticsearch 9.x security)

```bash
# Recuperer le token
docker-compose logs es01 | grep "Enrollment token"

# Ou generer un nouveau token
docker exec chapitre-1-es01 /usr/share/elasticsearch/bin/elasticsearch-create-enrollment-token -s kibana
```

Puis coller le token dans Kibana au premier lancement.

---

## Commandes de reference

```bash
# Cluster
curl localhost:9200/_cat/health?v
curl localhost:9200/_cluster/stats?pretty

# Indices
curl localhost:9200/_cat/indices?v
curl localhost:9200/_cat/nodes?v

# Documents
curl -X POST localhost:9200/products/_doc -H "Content-Type: application/json" -d '{...}'
curl -X GET localhost:9200/products/_search -H "Content-Type: application/json" -d '{"query": {...}}'
curl -X DELETE localhost:9200/products

# Bulk
curl -X POST localhost:9200/_bulk -H "Content-Type: application/json" --data-binary "@documents.json"
```

---

## Partie 6 : Rechercher des documents

### Etape 6.1 : Recuperer tous les documents

```bash
GET /products/_search
{
  "query": { "match_all": {} }
}
```

### Etape 6.2 : Recherche full-text

Rechercher "keyboard" dans `name` et `description` :

```bash
GET /products/_search
{
  "query": {
    "multi_match": {
      "query": "keyboard",
      "fields": ["name", "description"]
    }
  }
}
```

### Etape 6.3 : Filtrer par categorie

```bash
GET /products/_search
{
  "query": {
    "term": { "category": "Accessories" }
  }
}
```

### Etape 6.4 : Recherche avec plage de prix

Produits entre 50 et 200 EUR :

```bash
GET /products/_search
{
  "query": {
    "range": {
      "price": { "gte": 50, "lte": 200 }
    }
  }
}
```

### Etape 6.5 : Combiner plusieurs criteres (bool query)

Produits en stock ET prix < 100 EUR :

```bash
GET /products/_search
{
  "query": {
    "bool": {
      "must": [{ "term": { "in_stock": true } }],
      "filter": [{ "range": { "price": { "lt": 100 } } }]
    }
  }
}
```

---

## Partie 7 : Explorer dans Kibana

### Etape 7.1 : Creer un Data View (Index Pattern)

1. Menu (☰) → **Management** → **Stack Management**
2. Sous Kibana, selectionner **Data Views**
3. Cliquer sur **Create data view**
4. Remplir :
   - **Name** : `Products`
   - **Index pattern** : `products`
   - **Timestamp field** : `created_at`
5. Cliquer **Save data view to Kibana**

### Etape 7.2 : Explorer les donnees dans Discover

1. Menu (☰) → **Analytics** → **Discover**
2. Selectionner le data view `Products`
3. Utiliser la barre KQL pour filtrer :
   ```
   category: "Accessories"
   price > 100 and in_stock: true
   ```

### Etape 7.3 : Ajouter des colonnes

Dans **Available fields** (gauche), cliquer sur :
- `name`
- `price`
- `category`
- `in_stock`

Les colonnes s'ajoutent au tableau.

### Etape 7.4 : Sauvegarder la recherche

1. Cliquer **Save** (en haut a droite)
2. Nom : `Products overview`
3. Cliquer **Save**

---

## Partie 8 : Operations de gestion

### Etape 8.1 : Mettre a jour un document

```bash
POST /products/_update/1
{
  "doc": {
    "price": 139.99,
    "in_stock": false
  }
}
```

**Reponse :**
```json
{
  "_index": "products",
  "_id": "1",
  "_version": 2,
  "result": "updated"
}
```

### Etape 8.2 : Supprimer un document

```bash
DELETE /products/_doc/3
```

**Reponse :**
```json
{
  "_index": "products",
  "_id": "3",
  "_version": 2,
  "result": "deleted"
}
```

### Etape 8.3 : Supprimer tous les documents d'un index

```bash
POST /products/_delete_by_query
{
  "query": { "match_all": {} }
}
```

### Etape 8.4 : Fermer un index

```bash
POST /products/_close
```

Pour le rouvrir :
```bash
POST /products/_open
```

### Etape 8.5 : Supprimer un index

```bash
DELETE /products
```

> **Attention** : cette operation est irreversible.

---

## Resumé final

| Operation | Methode | Endpoint |
|-----------|---------|----------|
| Sante cluster | GET | `/_cat/health?v` |
| Creer index | PUT | `/nom_index` |
| Indexer doc | POST | `/nom_index/_doc/id` |
| Bulk index | POST | `/nom_index/_bulk` |
| Rechercher | GET | `/nom_index/_search` |
| Compter | GET | `/nom_index/_count` |
| Mettre a jour | POST | `/nom_index/_update/id` |
| Supprimer doc | DELETE | `/nom_index/_doc/id` |
| Supprimer index | DELETE | `/nom_index` |

### Etape 8.2 : Supprimer un document

```bash
DELETE /products/_doc/4
```

### Etape 8.3 : Consulter les statistiques de l'index

```bash
GET /products/_stats
```

### Etape 8.4 : Rafraichir l'index

```bash
POST /products/_refresh
```

> Par defaut ES rafraichit les index toutes les secondes. Cette commande force un rafraichissement immediat.

---

## Partie 9 (Bonus) : Configuration Logstash

### Etape 9.1 : Fichier de configuration Logstash

Creer `logstash/pipeline/logstash.conf` :

```conf
input {
  file {
    path => "/usr/share/logstash/data/sample.log"
    start_position => "beginning"
    sincedb_path => "/dev/null"
  }
}

filter {
  grok {
    match => { "message" => "%{COMBINEDAPACHELOG}" }
  }
  date {
    match => [ "timestamp", "dd/MMM/yyyy:HH:mm:ss Z" ]
  }
  geoip {
    source => "clientip"
  }
}

output {
  elasticsearch {
    hosts => ["es01:9200"]
    index => "apache-logs-%{+YYYY.MM.dd}"
  }
  stdout { codec => rubydebug }
}
```

### Etape 9.2 : Creer un log d'exemple

Creer `logstash/data/sample.log` :

```
192.168.1.100 - - [14/Jun/2026:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 2326
192.168.1.101 - - [14/Jun/2026:10:01:00 +0000] "POST /api/login HTTP/1.1" 401 0
192.168.1.102 - - [14/Jun/2026:10:02:00 +0000] "GET /products HTTP/1.1" 200 15234
```

### Etape 9.3 : Activer Logstash dans docker-compose.yml

Decommenter le service `logstash` dans `docker-compose.yml` puis :

```bash
docker-compose up -d
```

### Etape 9.4 : Verifier l'ingestion

```bash
# Suivre les logs
docker-compose logs -f logstash

# Verifier l'index cree
curl -X GET "localhost:9200/_cat/indices?v" | grep apache

# Rechercher dans l'index
GET /apache-logs-*/_search
```

---

## Troubleshooting

| Probleme | Cause | Solution |
|---------|-------|----------|
| ES ne demarre pas (boucle) | `vm.max_map_count` trop bas | `sudo sysctl -w vm.max_map_count=262144` |
| ES ne demarre pas | RAM Docker insuffisante | Allouer 4-8GB dans Docker Desktop |
| "Kibana server is not ready yet" | ES pas encore pret | Attendre 1-2 min, consulter `docker-compose logs kibana` |
| `bind: address already in use` | Port occupe | Modifier ports dans `docker-compose.yml` (ex: `9201:9200`) |
| `403 Forbidden / 401 Unauthorized` | Security active (9.x) | Ajouter `xpack.security.enabled=false` dans docker-compose.yml |
| `Content-Type header not supported` | Header manquant | Ajouter `-H "Content-Type: application/json"` dans curl |

---

## Nettoyage

```bash
# Arreter les conteneurs
docker-compose stop

# Arreter + supprimer les conteneurs
docker-compose down

# Arreter + supprimer les donnees (IRREVERSIBLE)
docker-compose down -v
```

---

## Criteres de validation du TP

- [ ] Le cluster Elasticsearch est en `green` ou `yellow`
- [ ] Kibana est accessible sur http://localhost:5601
- [ ] L'index `products` contient au moins 5 documents
- [ ] Les recherches via Dev Tools fonctionnent
- [ ] Un Data View a ete cree dans Kibana
- [ ] Les documents sont visibles dans Discover
- [ ] (Bonus) Logstash ingere des logs avec succes

---

## Pour aller plus loin

- **Aggregations** : `GET /products/_search` avec `aggs` pour calculer des statistiques par categorie
- **Aliases** : creer un alias `products-latest` pointant vers `products`
- **Snapshots** : sauvegarder les indices dans un bucket S3-compatible
- **ILM (Index Lifecycle Management)** : automatiser la rotation et suppression des anciens indices
- **Mapping dynamique** : decouvrir comment ES infere les types automatiquement
