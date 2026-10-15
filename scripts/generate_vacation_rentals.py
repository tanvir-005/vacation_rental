#!/usr/bin/env python3
"""Generate 2,000 deterministic synthetic Bangladesh vacation-rental rows.

Locality coordinates are approximate reference points; generated points are small
offsets from those points for spatial-search testing. Listings and image assignments
are synthetic, not real or verified rentals. Uses only Python's standard library.
"""
import argparse, csv, json, random
from pathlib import Path

DESTINATIONS = [("Cox's Bazar", 21.43973, 92.00955, [('Kolatoli', 21.413, 91.982), ('Sugandha', 21.427, 91.978), ('Laboni Beach', 21.435, 91.976), ('Marine Drive', 21.387, 92.006)], ['Beach Apartment', 'Coastal Guesthouse', 'Sea-View Studio', 'Family Suite'], (2200, 16000), 'beach'), ('Dhaka', 23.810332, 90.412518, [('Gulshan', 23.7925, 90.4078), ('Banani', 23.7937, 90.4066), ('Dhanmondi', 23.7461, 90.3742), ('Uttara', 23.8759, 90.3795), ('Bashundhara Residential Area', 23.8151, 90.4255)], ['City Apartment', 'Serviced Apartment', 'Modern Studio', 'Family Flat'], (1800, 18000), 'city'), ('Sylhet', 24.899044, 91.87198, [('Zindabazar', 24.894, 91.868), ('Shahjalal Uposhohor', 24.8845, 91.8945), ('Tilagor', 24.912, 91.906), ('Airport Road', 24.954, 91.87)], ['Garden Guesthouse', 'Family Apartment', 'Hillside Retreat', 'City Studio'], (1600, 13000), 'hill'), ('Chattogram', 22.356851, 91.783182, [('Panchlaish', 22.359, 91.821), ('Khulshi', 22.365, 91.801), ('Agrabad', 22.326, 91.812), ('Patenga', 22.236, 91.813)], ['City Apartment', 'Business Suite', 'Family Flat', 'Coastal Guesthouse'], (1500, 15000), 'city'), ("Saint Martin's Island", 20.6274, 92.3223, [('West Beach', 20.627, 92.323), ('North Beach', 20.635, 92.326), ('Island Village', 20.622, 92.326)], ['Island Bungalow', 'Beach Cottage', 'Sea-View Room', 'Eco Guesthouse'], (2500, 18000), 'island'), ('Bandarban', 22.195344, 92.219464, [('Bandarban Town', 22.1953, 92.2195), ('Meghla', 22.177, 92.194), ('Nilachal', 22.174, 92.203), ('Milanchari', 22.166, 92.211)], ['Hill Cottage', 'Nature Lodge', 'Wooden Cabin', 'Family Guesthouse'], (1700, 13500), 'hill'), ('Rangamati', 22.643168, 92.191859, [('Reserve Bazar', 22.633, 92.2), ('Tabalchhari', 22.638, 92.208), ('Kaptai Lake Area', 22.65, 92.18)], ['Lake-View Cottage', 'Hill Retreat', 'Family Guesthouse', 'Wooden Cabin'], (1700, 14000), 'hill'), ('Kuakata', 21.8167, 90.1167, [('Kuakata Beach Road', 21.816, 90.116), ('Zero Point', 21.817, 90.118), ('Lemua', 21.82, 90.11)], ['Beach Cottage', 'Coastal Villa', 'Family Guesthouse', 'Sea-View Apartment'], (1800, 14500), 'beach'), ('Rajshahi', 24.363589, 88.624135, [('Shaheb Bazar', 24.374, 88.604), ('Laxmipur', 24.366, 88.609), ('Padma Residential Area', 24.358, 88.601)], ['City Apartment', 'Family Flat', 'Serviced Apartment', 'Garden Guesthouse'], (1200, 11000), 'city'), ('Khulna', 22.845641, 89.540328, [('Sonadanga', 22.833, 89.54), ('Khalishpur', 22.866, 89.536), ('Boyra', 22.833, 89.514), ('Nirala', 22.829, 89.545)], ['City Apartment', 'Family Flat', 'Serviced Apartment', 'Garden Guesthouse'], (1200, 12000), 'city')]
AMENITIES = {
 "beach": ["WiFi","Air conditioning","Kitchen","Free parking","Balcony","Sea view","Hot water","TV","Breakfast","Family rooms","Backup power"],
 "island": ["WiFi","Fan","Air conditioning","Breakfast","Sea view","Mosquito net","Hot water","Family rooms","Restaurant access","Solar power"],
 "hill": ["WiFi","Hot water","Free parking","Mountain view","Balcony","Breakfast","Garden","Family rooms","Backup power","Restaurant access"],
 "city": ["WiFi","Air conditioning","Kitchen","Free parking","Washer","Workspace","TV","Elevator","Security","Backup power","Hot water"],
}
IMAGES = ['https://images.unsplash.com/photo-1600585154340-be6161a56a0c', 'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c', 'https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea', 'https://images.unsplash.com/photo-1600607687920-4e2a09cf159d', 'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3', 'https://images.unsplash.com/photo-1600607687644-c7171b42498f', 'https://images.unsplash.com/photo-1600566752355-35792bedcfea']
FIELDS = ["property_id","title","description","city","country","latitude","longitude","address","price_per_night","max_guests","amenities","image_urls"]

def generate(output, count=2000, seed=42):
    if count < 1: raise ValueError("--count must be at least 1")
    rng = random.Random(seed)
    schedule = [DESTINATIONS[i % len(DESTINATIONS)] for i in range(count)]
    rng.shuffle(schedule)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS); writer.writeheader()
        for i, dest in enumerate(schedule, 1):
            city, center_lat, center_lon, areas, types, price_range, profile = dest
            country = 'Bangladesh'
            area, alat, alon = rng.choice(areas)
            kind = rng.choice(types)
            lat, lon = alat + rng.uniform(-0.0015,0.0015), alon + rng.uniform(-0.0015,0.0015)
            guests = rng.choices([1,2,3,4,5,6,8,10], weights=[3,12,10,28,12,18,12,5], k=1)[0]
            low, high = price_range
            multiplier = 1.25 if ("Serviced" in kind or "Villa" in kind) else 0.8 if ("Studio" in kind or "Room" in kind) else 1.0
            price = round((rng.uniform(low, high)*multiplier)/50)*50
            amenity_list = rng.sample(AMENITIES[profile], k=rng.randint(4,min(8,len(AMENITIES[profile]))))
            image_list = rng.sample(IMAGES, k=rng.randint(1,3))
            writer.writerow({
              "property_id": f"BD-SYN-{i:06d}", "title": f"{kind} in {area}",
              "description": f"Synthetic demonstration listing in {area}, {city}, Bangladesh. Designed for testing spatial search, distance calculations, amenity display, pagination, and semantic location search. Not a verified rental.",
              "city": city, "country": country, "latitude": f"{lat:.6f}", "longitude": f"{lon:.6f}",
              "address": f"{area}, {city}, {country}", "price_per_night": f"{price:.2f}",
              "max_guests": str(guests), "amenities": json.dumps(amenity_list, ensure_ascii=False),
              "image_urls": json.dumps(image_list, ensure_ascii=False)
            })

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--count", type=int, default=2000); p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", type=Path, default=Path("data/properties_v2.csv"))
    a=p.parse_args(); generate(a.output,a.count,a.seed)
    print(f"Generated {a.count:,} synthetic listings: {a.output}")
    print("Coordinates are approximate locality-based test points; listings are not verified rentals.")
if __name__ == "__main__": main()