#!/usr/bin/env python3
"""
TP3 Airbnb Dataset Generator
Genere 50,000+ listings Airbnb multi-villes pour le TP Elasticsearch 9.4.2.
"""

import json
import random
import argparse
from datetime import datetime, timedelta
from faker import Faker

fake = Faker(['fr_FR', 'en_US', 'en_GB', 'es_ES', 'nl_NL'])

CITIES = {
    'Paris':       {'lat': 48.8566, 'lon': 2.3522,  'country': 'France',     'currency': 'EUR'},
    'New York':    {'lat': 40.7128, 'lon': -74.0060, 'country': 'USA',        'currency': 'USD'},
    'London':      {'lat': 51.5074, 'lon': -0.1278,  'country': 'UK',         'currency': 'GBP'},
    'Barcelona':   {'lat': 41.3851, 'lon': 2.1734,   'country': 'Spain',       'currency': 'EUR'},
    'Amsterdam':   {'lat': 52.3676, 'lon': 4.9041,   'country': 'Netherlands','currency': 'EUR'},
}

PROPERTY_TYPES = ['Apartment', 'House', 'Studio', 'Loft', 'Condominium', 'Townhouse']
ROOM_TYPES = ['Entire home/apt', 'Private room', 'Shared room']
AMENITIES = [
    'Wifi', 'Kitchen', 'Heating', 'Washer', 'Essentials', 'TV', 'AC',
    'Pool', 'Gym', 'Parking', 'Balcony', 'Coffee machine', 'Dishwasher',
    'Iron', 'Hair dryer', 'Smoke alarm', 'First aid kit', 'Laptop workspace'
]
CANCELLATION_POLICIES = ['flexible', 'moderate', 'strict']

REVIEWS_COMMENTS = [
    "Amazing place! Highly recommended.",
    "Great location, clean and comfortable.",
    "Perfect for our stay, would come back.",
    "Very responsive host, everything was as described.",
    "Good value for money, central location.",
    "Spacious apartment with all amenities.",
    "Quiet neighborhood, easy access to public transport.",
    "Beautiful view, exceeded expectations.",
    "Clean, modern, and well-equipped.",
    "Ideal for families, lots of space.",
]


def gen_location(city_latlon: dict) -> dict:
    return {
        'lat': round(city_latlon['lat'] + random.uniform(-0.08, 0.08), 6),
        'lon': round(city_latlon['lon'] + random.uniform(-0.08, 0.08), 6),
    }


def gen_reviews(n: int) -> list:
    return [
        {
            'review_id': f'r{i+1}',
            'reviewer_name': fake.name(),
            'date': (datetime(2025, 1, 1) + timedelta(days=random.randint(0, 520))).strftime('%Y-%m-%d'),
            'rating': random.choice([3, 4, 4, 4, 5, 5, 5]),
            'comment': random.choice(REVIEWS_COMMENTS),
        }
        for i in range(n)
    ]


def gen_listing(idx: int, city: str, city_data: dict) -> dict:
    price = round(random.uniform(30, 500), 2)
    accommodates = random.randint(1, 8)
    bedrooms = random.randint(1, accommodates)
    beds = random.randint(1, bedrooms + 1)
    n_reviews = random.randint(0, 200)
    rating = round(random.uniform(3.0, 5.0), 1)
    host_since = (datetime(2010, 1, 1) + timedelta(days=random.randint(0, 5000))).strftime('%Y-%m-%d')

    return {
        'listing_id': str(idx),
        'name': fake.sentence(nb_words=6)[:-1],
        'description': fake.paragraph(nb_sentences=3),
        'host': {
            'host_id': str(random.randint(10000, 99999)),
            'host_name': fake.name(),
            'host_since': host_since,
            'host_response_rate': random.choice([80, 90, 95, 98, 100]),
            'host_is_superhost': random.random() < 0.25,
        },
        'location': gen_location(city_data),
        'address': {
            'street': fake.street_address(),
            'city': city,
            'country': city_data['country'],
            'zipcode': fake.postcode(),
            'neighborhood': fake.word().capitalize() + ' Quarter',
        },
        'property_type': random.choice(PROPERTY_TYPES),
        'room_type': random.choice(ROOM_TYPES),
        'accommodates': accommodates,
        'bedrooms': bedrooms,
        'beds': beds,
        'bathrooms': round(random.uniform(1, 4) * 2) / 2,
        'amenities': random.sample(AMENITIES, random.randint(4, 12)),
        'price': price,
        'currency': city_data['currency'],
        'minimum_nights': random.choice([1, 2, 3, 5, 7]),
        'maximum_nights': random.choice([30, 60, 90, 180, 365]),
        'availability_365': random.randint(30, 350),
        'number_of_reviews': n_reviews,
        'rating': rating,
        'reviews': gen_reviews(random.randint(0, 5)) if n_reviews > 0 else [],
        'instant_bookable': random.random() < 0.7,
        'cancellation_policy': random.choice(CANCELLATION_POLICIES),
        'created_at': host_since,
        'last_updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
    }


def generate_dataset(total: int = 50000, output: str = 'airbnb-listings.json') -> None:
    print(f'Generating {total:,} Airbnb listings...')
    listings = []
    per_city = total // len(CITIES)

    for city, city_data in CITIES.items():
        print(f'  {city}: ~{per_city:,} listings')
        for i in range(per_city):
            idx = len(listings) + 1
            listings.append(gen_listing(idx, city, city_data))

    # Fill remainder
    while len(listings) < total:
        city, city_data = random.choice(list(CITIES.items()))
        listings.append(gen_listing(len(listings) + 1, city, city_data))

    random.shuffle(listings)

    with open(output, 'w', encoding='utf-8') as f:
        for doc in listings:
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')

    print(f'Done — {len(listings):,} listings written to {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='TP3 Airbnb dataset generator')
    parser.add_argument('--count', type=int, default=50000, help='Total listings')
    parser.add_argument('--output', type=str, default='airbnb-listings.json')
    args = parser.parse_args()
    generate_dataset(args.count, args.output)
