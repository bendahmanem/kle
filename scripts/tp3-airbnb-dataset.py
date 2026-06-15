#!/usr/bin/env python3
"""
TP3 - Dataset Airbnb Generator + Indexer
Corrigé complet - ELK Stack 9.4.2
"""

import json
import random
import argparse
from datetime import datetime, timedelta
from faker import Faker

fake = Faker(['fr_FR', 'en_US', 'en_GB', 'es_ES', 'nl_NL'])

CITIES = {
    'Paris': {'lat': 48.8566, 'lon': 2.3522, 'currency': 'EUR', 'country': 'France'},
    'New York': {'lat': 40.7128, 'lon': -74.0060, 'currency': 'USD', 'country': 'USA'},
    'London': {'lat': 51.5074, 'lon': -0.1278, 'currency': 'GBP', 'country': 'UK'},
    'Barcelona': {'lat': 41.3851, 'lon': 2.1734, 'currency': 'EUR', 'country': 'Spain'},
    'Amsterdam': {'lat': 52.3676, 'lon': 4.9041, 'currency': 'EUR', 'country': 'Netherlands'},
}

PROPERTY_TYPES = ['Apartment', 'House', 'Studio', 'Loft', 'Condo', 'Villa', 'Townhouse']
ROOM_TYPES = ['Entire home/apt', 'Private room', 'Shared room']
AMENITIES_POOL = [
    'Wifi', 'Kitchen', 'Heating', 'Washer', 'Essentials', 'TV', 'Air conditioning',
    'Coffee machine', 'Dishwasher', 'Microwave', 'Refrigerator', 'Oven', 'Hair dryer',
    'Iron', 'Laptop workspace', 'Elevator', 'Gym', 'Pool', 'Hot tub', 'Parking',
    'Balcony', 'Garden', 'Terrace', 'BBQ', 'Fireplace', 'Doorman', 'Security camera',
    'Smoke detector', 'Carbon monoxide detector', 'First aid kit', 'Lockbox'
]
CANCELLATION_POLICIES = ['flexible', 'moderate', 'strict', 'strict_2', 'strict_3', 'super_strict_30', 'super_strict_60']

REVIEWS_COMMENTS = [
    "Amazing place! Highly recommended.", "Great location, clean and comfortable.",
    "Perfect for our stay. Would come back!", "Beautiful apartment, very spacious.",
    "Excellent host, very responsive.", "Ideal location, everything walking distance.",
    "Clean, modern, great amenities.", "Cozy place, loved the decor.",
    "Superb stay, exceeded expectations.", "Good value for money, recommended.",
    "Fantastic location and view.", "Very quiet neighborhood, enjoyed the stay.",
    "Host was very helpful with check-in.", "Place was exactly as described.",
    "Would definitely book again.", "Great for families, lots of space.",
]


def generate_listing(listing_id, city_name, city_data):
    """Génère un listing Airbnb réaliste."""
    lat_offset = random.gauss(0, 0.05)
    lon_offset = random.gauss(0, 0.05)
    lat = round(city_data['lat'] + lat_offset, 6)
    lon = round(city_data['lon'] + lon_offset, 6)

    accommodates = random.randint(1, 10)
    bedrooms = max(1, random.randint(1, accommodates))
    beds = max(bedrooms, random.randint(bedrooms, accommodates + 2))
    bathrooms = round(random.choice([1, 1.5, 2, 2.5, 3, 3.5, 4]), 1)

    base_price = random.randint(40, 500)
    if city_name == 'Paris':
        base_price = int(base_price * 1.2)
    elif city_name == 'New York':
        base_price = int(base_price * 1.3)
    price = round(base_price * random.uniform(0.8, 1.5), 2)

    host_since = fake.date_between(start_date='-10y', end_date='-1y')
    host_response_rate = random.choice([90, 95, 98, 99, 100])
    host_is_superhost = random.random() < 0.2

    num_reviews = random.choices(
        [0, random.randint(1, 10), random.randint(11, 50), random.randint(51, 200)],
        weights=[0.1, 0.4, 0.35, 0.15]
    )[0]
    rating = round(random.uniform(3.5, 5.0), 1) if num_reviews > 0 else None

    num_amenities = random.randint(5, 20)
    amenities = random.sample(AMENITIES_POOL, num_amenities)

    reviews = []
    for i in range(num_reviews):
        review_date = fake.date_between(start_date=host_since, end_date='today')
        review_rating = random.choices([3, 4, 5], weights=[0.05, 0.2, 0.75])[0]
        reviews.append({
            'review_id': f'r{listing_id}-{i + 1}',
            'reviewer_name': fake.first_name(),
            'date': review_date.isoformat(),
            'rating': review_rating,
            'comment': random.choice(REVIEWS_COMMENTS),
        })

    created_at = host_since
    last_updated = fake.date_between(start_date=created_at, end_date='today')

    neighborhoods = {
        'Paris': ['Le Marais', 'Montmartre', 'Latin Quarter', 'Champs-Élysées', 'Bastille', 'Saint-Germain', 'Belleville', 'Oberkampf'],
        'New York': ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Harlem', 'SoHo', 'Tribeca', 'Williamsburg'],
        'London': ['Westminster', 'Camden', 'Shoreditch', 'Notting Hill', 'Covent Garden', 'Hackney', 'Kensington', 'Chelsea'],
        'Barcelona': ['Gràcia', 'El Born', 'Gothic Quarter', 'Eixample', 'Barceloneta', 'Montjuïc', 'Poblenou', 'Sant Antoni'],
        'Amsterdam': ['Jordaan', 'De Pijp', 'Vondelpark', 'Canal Belt', 'Anne Frank', 'Museum Quarter', ' Westerpark', 'Noord'],
    }
    neighborhood = random.choice(neighborhoods.get(city_name, ['Downtown']))

    return {
        'listing_id': str(listing_id),
        'name': f"{random.choice(['Cozy', 'Modern', 'Beautiful', 'Spacious', 'Charming', 'Bright', 'Stylish', 'Luxury'])} {random.choice(PROPERTY_TYPES).lower()} in {neighborhood}",
        'description': fake.paragraph(nb_sentences=4),
        'host': {
            'host_id': str(random.randint(10000, 99999)),
            'host_name': fake.first_name(),
            'host_since': host_since.isoformat(),
            'host_response_rate': host_response_rate,
            'host_is_superhost': host_is_superhost,
        },
        'location': {'lat': lat, 'lon': lon},
        'address': {
            'street': fake.street_address(),
            'city': city_name,
            'country': city_data['country'],
            'zipcode': fake.postcode(),
            'neighborhood': neighborhood,
        },
        'property_type': random.choice(PROPERTY_TYPES),
        'room_type': random.choice(ROOM_TYPES),
        'accommodates': accommodates,
        'bedrooms': bedrooms,
        'beds': beds,
        'bathrooms': bathrooms,
        'amenities': amenities,
        'price': price,
        'currency': city_data['currency'],
        'minimum_nights': random.choice([1, 2, 3, 5, 7]),
        'maximum_nights': random.choice([30, 60, 90, 180, 365]),
        'availability_365': random.randint(0, 365),
        'number_of_reviews': num_reviews,
        'rating': rating,
        'reviews': reviews,
        'instant_bookable': random.random() < 0.6,
        'cancellation_policy': random.choice(CANCELLATION_POLICIES),
        'created_at': created_at.isoformat(),
        'last_updated': last_updated.isoformat(),
    }


def generate_dataset(count=50000):
    """Génère le dataset complet."""
    listings = []
    per_city = count // len(CITIES)
    listing_id = 1

    for city_name, city_data in CITIES.items():
        for _ in range(per_city):
            listings.append(generate_listing(listing_id, city_name, city_data))
            listing_id += 1

    print(f"✅ Dataset généré : {len(listings)} listings")
    return listings


def save_dataset(listings, filepath='airbnb-listings.json'):
    """Sauvegarde le dataset."""
    with open(filepath, 'w', encoding='utf-8') as f:
        for listing in listings:
            f.write(json.dumps(listing, ensure_ascii=False) + '\n')
    print(f"💾 Dataset sauvegardé : {filepath}")


def index_dataset(filepath='airbnb-listings.json', es_host='http://localhost:9200', batch_size=1000):
    """Indexe le dataset dans Elasticsearch via Bulk API."""
    import requests

    # Vérifier ES
    try:
        r = requests.get(f"{es_host}/_cluster/health", timeout=10)
        if r.status_code != 200:
            print(f"❌ Elasticsearch pas prêt : {r.status_code}")
            return
        print(f"✅ Elasticsearch prêt : {r.json()['cluster_name']}")
    except Exception as e:
        print(f"❌ Connexion ES échouée : {e}")
        return

    # Créer l'index avec mapping
    mapping = {
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
                "listing_id": {"type": "keyword"},
                "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "description": {"type": "text"},
                "host": {
                    "properties": {
                        "host_id": {"type": "keyword"},
                        "host_name": {"type": "keyword"},
                        "host_since": {"type": "date"},
                        "host_response_rate": {"type": "byte"},
                        "host_is_superhost": {"type": "boolean"}
                    }
                },
                "location": {"type": "geo_point"},
                "address": {
                    "properties": {
                        "street": {"type": "text", "analyzer": "address_analyzer"},
                        "city": {"type": "keyword"},
                        "country": {"type": "keyword"},
                        "zipcode": {"type": "keyword"},
                        "neighborhood": {"type": "keyword", "fields": {"text": {"type": "text"}}}
                    }
                },
                "property_type": {"type": "keyword"},
                "room_type": {"type": "keyword"},
                "accommodates": {"type": "integer"},
                "bedrooms": {"type": "integer"},
                "beds": {"type": "integer"},
                "bathrooms": {"type": "half_float"},
                "amenities": {"type": "keyword"},
                "price": {"type": "float"},
                "currency": {"type": "keyword"},
                "minimum_nights": {"type": "short"},
                "maximum_nights": {"type": "short"},
                "availability_365": {"type": "short"},
                "number_of_reviews": {"type": "integer"},
                "rating": {"type": "half_float"},
                "reviews": {
                    "type": "nested",
                    "properties": {
                        "review_id": {"type": "keyword"},
                        "reviewer_name": {"type": "keyword"},
                        "date": {"type": "date"},
                        "rating": {"type": "byte"},
                        "comment": {"type": "text"}
                    }
                },
                "instant_bookable": {"type": "boolean"},
                "cancellation_policy": {"type": "keyword"},
                "created_at": {"type": "date"},
                "last_updated": {"type": "date"}
            }
        }
    }

    # Supprimer l'index existant
    r = requests.delete(f"{es_host}/airbnb-listings", timeout=30)
    print(f"🗑️  Index supprimé (si existait) : {r.status_code}")

    # Créer le nouvel index
    r = requests.put(f"{es_host}/airbnb-listings", json=mapping, timeout=30)
    if r.status_code not in (200, 201):
        print(f"❌ Création index échouée : {r.text}")
        return
    print("✅ Index 'airbnb-listings' créé")

    # Indexer par batch
    with open(filepath, 'r', encoding='utf-8') as f:
        batch = []
        total = 0
        for line in f:
            batch.append({"index": {"_index": "airbnb-listings"}})
            batch.append(json.loads(line))
            if len(batch) >= batch_size * 2:
                r = requests.post(f"{es_host}/_bulk", json=batch, timeout=60)
                total += batch_size
                print(f"  Indexé {total} documents...")
                batch = []

        if batch:
            r = requests.post(f"{es_host}/_bulk", json=batch, timeout=60)
            total += len(batch) // 2
            print(f"  Indexé {total} documents...")

    # Optimisations post-indexation
    print("\n⚡ Optimisations...")
    requests.put(f"{es_host}/airbnb-listings/_settings", json={"index.refresh_interval": "1s"})
    requests.post(f"{es_host}/airbnb-listings/_forcemerge?max_num_segments=1", timeout=60)
    requests.post(f"{es_host}/airbnb-listings/_refresh")

    r = requests.get(f"{es_host}/airbnb-listings/_count")
    count = r.json()['count']
    print(f"\n🎉 Indexation terminée : {count} documents dans l'index")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TP3 Airbnb Dataset Generator + Indexer')
    parser.add_argument('--index', action='store_true', help='Générer + indexer dans ES')
    parser.add_argument('--count', type=int, default=50000, help='Nombre de listings (défaut: 50000)')
    parser.add_argument('--host', type=str, default='http://localhost:9200', help='Host ES')
    args = parser.parse_args()

    if args.index:
        # Générer + indexer
        listings = generate_dataset(args.count)
        save_dataset(listings)
        index_dataset(es_host=args.host)
    else:
        # Générer seulement
        listings = generate_dataset(args.count)
        save_dataset(listings)
        print("\n📌 Pour indexer : python3 tp3-airbnb-dataset.py --index")