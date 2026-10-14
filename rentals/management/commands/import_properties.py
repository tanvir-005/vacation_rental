import csv
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from rentals.models import Location, Property, PropertyImage


class Command(BaseCommand):
    help = "Import vacation-rental properties from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=Path,
            help="Path to the properties CSV file.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Database batch size (default: 500).",
        )

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        batch_size = options["batch_size"]

        if batch_size < 1:
            raise CommandError("--batch-size must be greater than zero.")

        if not csv_file.is_file():
            raise CommandError(f"CSV file does not exist: {csv_file}")

        required_columns = {
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
        }

        try:
            with csv_file.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)

                missing = required_columns - set(reader.fieldnames or [])
                if missing:
                    raise CommandError(
                        f"Missing CSV columns: {', '.join(sorted(missing))}"
                    )

                rows = list(reader)

            if not rows:
                self.stdout.write(self.style.WARNING("CSV contains no data rows."))
                return

            # Validate every row before making database changes.
            validated = []
            errors = []

            for line_number, row in enumerate(rows, start=2):
                try:
                    property_id = row["property_id"].strip()
                    title = row["title"].strip()
                    city = row["city"].strip()
                    country = row["country"].strip()

                    if not all((property_id, title, city, country)):
                        raise ValueError("property_id, title, city, and country are required")

                    latitude = float(row["latitude"])
                    longitude = float(row["longitude"])

                    if not -90 <= latitude <= 90:
                        raise ValueError("latitude must be between -90 and 90")
                    if not -180 <= longitude <= 180:
                        raise ValueError("longitude must be between -180 and 180")

                    price = Decimal(row["price_per_night"])
                    if not price.is_finite() or price < 0:
                        raise ValueError("price_per_night must be a finite non-negative number")

                    max_guests = int(row["max_guests"])
                    if max_guests < 1:
                        raise ValueError("max_guests must be at least 1")

                    amenities = json.loads(row["amenities"])
                    image_urls = json.loads(row["image_urls"])

                    if not isinstance(amenities, list):
                        raise ValueError("amenities must be a JSON array")
                    if not all(isinstance(item, str) for item in amenities):
                        raise ValueError("every amenity must be a string")
                    if not isinstance(image_urls, list):
                        raise ValueError("image_urls must be a JSON array")
                    if not all(isinstance(url, str) and url.startswith(("https://", "http://"))
                               for url in image_urls):
                        raise ValueError("every image URL must begin with http:// or https://")

                    validated.append({
                        "property_id": property_id,
                        "title": title,
                        "description": row["description"].strip(),
                        "city": city,
                        "country": country,
                        "latitude": latitude,
                        "longitude": longitude,
                        "address": row["address"].strip(),
                        "price": price,
                        "max_guests": max_guests,
                        "amenities": amenities,
                        "image_urls": list(dict.fromkeys(image_urls)),
                    })

                except (ValueError, TypeError, KeyError, InvalidOperation, json.JSONDecodeError) as exc:
                    errors.append(f"Line {line_number}: {exc}")

            if errors:
                preview = "\n".join(errors[:20])
                extra = len(errors) - min(len(errors), 20)
                if extra:
                    preview += f"\n... and {extra} more error(s)"
                raise CommandError(
                    f"CSV validation failed with {len(errors)} error(s):\n{preview}"
                )

            property_ids = [row["property_id"] for row in validated]
            if len(property_ids) != len(set(property_ids)):
                raise CommandError("CSV contains duplicate property_id values.")

            # All writes are atomic: a failure rolls back the entire import.
            with transaction.atomic():
                city_coordinates = {}

                for row in validated:
                    key = (row["city"], row["country"])

                    if key not in city_coordinates:
                        city_coordinates[key] = {
                            "latitude": 0.0,
                            "longitude": 0.0,
                            "count": 0,
                        }

                    city_coordinates[key]["latitude"] += row["latitude"]
                    city_coordinates[key]["longitude"] += row["longitude"]
                    city_coordinates[key]["count"] += 1

                locations = {}

                for (city, country), coordinates in city_coordinates.items():
                    count = coordinates["count"]

                    latitude = coordinates["latitude"] / count
                    longitude = coordinates["longitude"] / count

                    location_name = f"{city}, {country}"

                    location, _ = Location.objects.get_or_create(
                        name=location_name,
                    )

                    location.point = Point(
                        longitude,
                        latitude,
                        srid=4326,
                    )
                    location.save(update_fields=["point", "updated_at"])

                    locations[(city, country)] = location
                # for city, country in sorted(cities):
                #     # The current Location model stores only a unique name.
                #     # Include country in the name to avoid cross-country collisions.
                #     location_name = f"{city}, {country}"
                #     location, _ = Location.objects.get_or_create(name=location_name)
                #     locations[(city, country)] = location

                existing_ids = set(
                    Property.objects.filter(
                        import_id__in=property_ids
                    ).values_list("import_id", flat=True)
                )

                new_properties = []
                property_rows = []

                for row in validated:
                    if row["property_id"] in existing_ids:
                        continue

                    prop = Property(
                        location=locations[(row["city"], row["country"])],
                        title=row["title"],
                        description=row["description"],
                        address=row["address"],
                        point=Point(row["longitude"], row["latitude"], srid=4326),
                        amenities=row["amenities"],
                        price_per_night=row["price"],
                        max_guests=row["max_guests"],
                        import_id=row["property_id"],
                    )
                    new_properties.append(prop)
                    property_rows.append(row)

                Property.objects.bulk_create(new_properties, batch_size=batch_size)

                images = []
                for prop, row in zip(new_properties, property_rows):
                    for url in row["image_urls"]:
                        images.append(
                            PropertyImage(
                                property=prop,
                                image_url=url,
                            )
                        )

                PropertyImage.objects.bulk_create(images, batch_size=batch_size)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Import complete: {len(new_properties)} new properties, "
                    f"{len(images)} image URLs, "
                    f"{len(validated) - len(new_properties)} existing properties skipped."
                )
            )

        except OSError as exc:
            raise CommandError(f"Could not read CSV: {exc}") from exc

