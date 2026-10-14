#!/usr/bin/env python3
"""Generate deterministic synthetic vacation-rental data for the Django assignment.

This script uses only the Python standard library. It does not import Django,
connect to a database, or download images.

Example:
    python generate_vacation_rentals.py
    python generate_vacation_rentals.py --count 2500 --seed 7 --output data/properties.csv
"""

import argparse
import csv
import json
import random
from pathlib import Path


# Approximate city centers in Bangladesh: (latitude, longitude).
# Generated coordinates are synthetic points near these centers, not verified
# property addresses or a claim that a rental exists at that location.
LOCATIONS = [
    {
        "city": "Cox's Bazar",
        "country": "Bangladesh",
        "latitude": 21.4272,
        "longitude": 91.9702,
        "areas": ["Kolatoli", "Sugandha", "Laboni Beach Road", "Marine Drive"],
        "property_types": ["Beachfront Apartment", "Coastal Villa", "Family Guesthouse", "Sea-View Studio"],
    },
    {
        "city": "Dhaka",
        "country": "Bangladesh",
        "latitude": 23.8103,
        "longitude": 90.4125,
        "areas": ["Gulshan", "Banani", "Dhanmondi", "Uttara", "Bashundhara"],
        "property_types": ["City Apartment", "Serviced Apartment", "Modern Studio", "Family Flat"],
    },
    {
        "city": "Sylhet",
        "country": "Bangladesh",
        "latitude": 24.8949,
        "longitude": 91.8687,
        "areas": ["Zindabazar", "Shahjalal Uposhohor", "Tilagor", "Airport Road"],
        "property_types": ["Garden Cottage", "Family Guesthouse", "Hillside Retreat", "City Apartment"],
    },
    {
        "city": "Chattogram",
        "country": "Bangladesh",
        "latitude": 22.3569,
        "longitude": 91.7832,
        "areas": ["Panchlaish", "Khulshi", "Agrabad", "Patenga"],
        "property_types": ["City Apartment", "Business Suite", "Family Flat", "Coastal Guesthouse"],
    },
    {
        "city": "Saint Martin's Island",
        "country": "Bangladesh",
        "latitude": 20.6274,
        "longitude": 92.3223,
        "areas": ["West Beach", "North Beach", "Island Village"],
        "property_types": ["Island Bungalow", "Beach Cottage", "Sea-View Room", "Eco Guesthouse"],
    },
    {
        "city": "Bandarban",
        "country": "Bangladesh",
        "latitude": 22.1953,
        "longitude": 92.2184,
        "areas": ["Meghla", "Nilachal", "Bandarban Town", "Chimbuk Road"],
        "property_types": ["Hilltop Cottage", "Nature Lodge", "Wooden Cabin", "Family Guesthouse"],
    },
    {
        "city": "Rangamati",
        "country": "Bangladesh",
        "latitude": 22.7324,
        "longitude": 92.2985,
        "areas": ["Kaptai Lake", "Reserve Bazar", "Tabalchhari"],
        "property_types": ["Lake-View Cottage", "Hill Retreat", "Family Guesthouse", "Wooden Cabin"],
    },
    {
        "city": "Kuakata",
        "country": "Bangladesh",
        "latitude": 21.8167,
        "longitude": 90.1167,
        "areas": ["Beach Road", "Zero Point", "Lemua"],
        "property_types": ["Beach Cottage", "Coastal Villa", "Family Guesthouse", "Sea-View Apartment"],
    },
    {
        "city": "Rajshahi",
        "country": "Bangladesh",
        "latitude": 24.3745,
        "longitude": 88.6042,
        "areas": ["Shaheb Bazar", "Laxmipur", "Padma Residential Area"],
        "property_types": ["City Apartment", "Family Flat", "Serviced Apartment", "Garden Guesthouse"],
    },
    {
        "city": "Khulna",
        "country": "Bangladesh",
        "latitude": 22.8456,
        "longitude": 89.5403,
        "areas": ["Sonadanga", "Khalishpur", "Boyra", "Nirala"],
        "property_types": ["City Apartment", "Family Flat", "Serviced Apartment", "Garden Guesthouse"],
    },
]

AMENITIES = [
    "WiFi",
    "Air conditioning",
    "Kitchen",
    "Free parking",
    "Washer",
    "Workspace",
    "TV",
    "Balcony",
    "Swimming pool",
    "Breakfast",
    "Garden",
    "Pet-friendly",
    "Hot water",
    "Security",
    "Generator backup",
]

# These are example external image URLs, not locally stored image files.
# Keep them as data in the CSV; the importer should not download them.
IMAGE_URLS = [
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c",
    "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea",
    "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d",
    "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3",
    "https://images.unsplash.com/photo-1600607687644-c7171b42498f",
    "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d",
    "https://images.unsplash.com/photo-1600566752355-35792bedcfea",
]

FIELDNAMES = [
    "property_id",
    "title",
    "description",
    "city",
    "country",
    "latitude",
    "longitude",
    "address",
    "price_per_night",
    "max_guests",
    "amenities",
    "image_urls",
]


def build_property(index: int, rng: random.Random) -> dict[str, str]:
    location = rng.choice(LOCATIONS)
    property_type = rng.choice(location["property_types"])
    area = rng.choice(location["areas"])
    features = rng.sample(AMENITIES, k=rng.randint(3, 7))
    guests = rng.randint(1, 12)

    # Synthetic points jittered around approximate city centers.
    # Keep jitter modest; these are test coordinates, not real listings.
    latitude = location["latitude"] + rng.uniform(-0.045, 0.045)
    longitude = location["longitude"] + rng.uniform(-0.045, 0.045)

    # Broad synthetic price bands in BDT, varied by destination.
    if location["city"] in {"Cox's Bazar", "Saint Martin's Island", "Kuakata"}:
        low, high = 1800, 18000
    elif location["city"] in {"Bandarban", "Rangamati", "Sylhet"}:
        low, high = 1500, 14000
    else:
        low, high = 1200, 16000

    price = round(rng.uniform(low, high) / 50) * 50
    title = f"{property_type} near {area}"
    description = (
        f"Synthetic sample listing for testing search and filtering. "
        f"This {property_type.lower()} is placed in the {area} area of "
        f"{location['city']}. Amenities and coordinates are generated test data."
    )
    selected_images = rng.sample(IMAGE_URLS, k=rng.randint(1, 3))

    return {
        "property_id": f"PROP-{index:06d}",
        "title": title,
        "description": description,
        "city": location["city"],
        "country": location["country"],
        "latitude": f"{latitude:.6f}",
        "longitude": f"{longitude:.6f}",
        "address": f"{area}, {location['city']}, Bangladesh",
        "price_per_night": f"{price:.2f}",
        "max_guests": str(guests),
        # JSON arrays are valid CSV cell values when correctly quoted.
        "amenities": json.dumps(features, ensure_ascii=False),
        "image_urls": json.dumps(selected_images, ensure_ascii=False),
    }


def generate_csv(output: Path, count: int, seed: int) -> None:
    if count < 1:
        raise ValueError("--count must be at least 1")

    rng = random.Random(seed)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        for index in range(1, count + 1):
            writer.writerow(build_property(index, rng))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1000, help="number of rows (default: 1000)")
    parser.add_argument("--seed", type=int, default=42, help="random seed for reproducible output (default: 42)")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/properties.csv"),
        help="output CSV path (default: data/properties.csv)",
    )
    args = parser.parse_args()

    generate_csv(args.output, args.count, args.seed)
    print(f"Generated {args.count:,} synthetic properties: {args.output}")
    print(f"Random seed: {args.seed}")
    print("Reminder: listings, coordinates, prices, and amenities are synthetic.")


if __name__ == "__main__":
    main()
