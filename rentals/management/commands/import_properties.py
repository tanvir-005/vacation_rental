import csv
import json
import pandas as pd
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
    
    def read_file(self, file_path):
        suffix = file_path.suffix.lower()

        try:
            if suffix == ".csv":
                with file_path.open(
                    "r", encoding="utf-8-sig", newline=""
                ) as file:
                    return list(csv.DictReader(file))

            if suffix == ".parquet":
                return pd.read_parquet(file_path).to_dict("records")

            if suffix in {".xlsx", ".xls"}:
                return pd.read_excel(file_path).to_dict("records")

        except (ValueError, ImportError) as exc:
            raise CommandError(
                f"Could not read {file_path.name}: {exc}"
            ) from exc

        raise CommandError(
            "Unsupported file format. Use .csv, .parquet, .xlsx, or .xls."
        )


    def handle(self, *args, **options):
        file_path = options["csv_file"]
        batch_size = options["batch_size"]

        if batch_size < 1:
            raise CommandError("--batch-size must be greater than zero.")

        if not file_path.is_file():
            raise CommandError(f"File does not exist: {file_path}")

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

        # Read CSV, Parquet, or Excel.
        try:
            suffix = file_path.suffix.lower()

            if suffix == ".csv":
                with file_path.open(
                    "r", encoding="utf-8-sig", newline=""
                ) as file:
                    rows = list(csv.DictReader(file))

            elif suffix == ".parquet":
                rows = pd.read_parquet(file_path).to_dict("records")

            elif suffix in {".xlsx", ".xls"}:
                rows = pd.read_excel(file_path).to_dict("records")

            else:
                raise CommandError(
                    "Unsupported format. Use .csv, .parquet, .xlsx, or .xls."
                )

        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(
                f"Could not read {file_path.name}: {exc}"
            ) from exc

        if not rows:
            self.stdout.write(
                self.style.WARNING("File contains no data rows.")
            )
            return

        missing = required_columns - set(rows[0].keys())
        if missing:
            raise CommandError(
                f"Missing columns: {', '.join(sorted(missing))}"
            )

        # Validate every row before making database changes.
        validated = []
        errors = []

        for line_number, row in enumerate(rows, start=2):
            try:
                # Pandas represents empty spreadsheet cells as NaN.
                row = {
                    key: (
                        ""
                        if value is None
                        or (
                            isinstance(value, float)
                            and pd.isna(value)
                        )
                        else str(value)
                        if not isinstance(value, (list, dict))
                        else json.dumps(value)
                    )
                    for key, value in row.items()
                }

                property_id = row["property_id"].strip()
                title = row["title"].strip()
                city = row["city"].strip()
                country = row["country"].strip()

                if not all((property_id, title, city, country)):
                    raise ValueError(
                        "property_id, title, city, and country are required"
                    )

                latitude = float(row["latitude"])
                longitude = float(row["longitude"])

                if not -90 <= latitude <= 90:
                    raise ValueError(
                        "latitude must be between -90 and 90"
                    )
                if not -180 <= longitude <= 180:
                    raise ValueError(
                        "longitude must be between -180 and 180"
                    )

                price = Decimal(row["price_per_night"])
                if not price.is_finite() or price < 0:
                    raise ValueError(
                        "price_per_night must be a finite non-negative number"
                    )

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
                if not all(
                    isinstance(url, str)
                    and url.startswith(("https://", "http://"))
                    for url in image_urls
                ):
                    raise ValueError(
                        "every image URL must begin with http:// or https://"
                    )

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

            except (
                ValueError,
                TypeError,
                KeyError,
                InvalidOperation,
                json.JSONDecodeError,
            ) as exc:
                errors.append(f"Row {line_number}: {exc}")

        if errors:
            preview = "\n".join(errors[:20])
            extra = len(errors) - min(len(errors), 20)

            if extra:
                preview += f"\n... and {extra} more error(s)"

            raise CommandError(
                f"File validation failed with {len(errors)} error(s):\n"
                f"{preview}"
            )

        property_ids = [row["property_id"] for row in validated]

        if len(property_ids) != len(set(property_ids)):
            raise CommandError("File contains duplicate property_id values.")

        with transaction.atomic():
            # Calculate representative coordinates for each city.
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

                location, _ = Location.objects.get_or_create(
                    name=f"{city}, {country}"
                )

                location.point = Point(longitude, latitude, srid=4326)
                location.save(update_fields=["point", "updated_at"])

                locations[(city, country)] = location

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
                    point=Point(
                        row["longitude"],
                        row["latitude"],
                        srid=4326,
                    ),
                    amenities=row["amenities"],
                    price_per_night=row["price"],
                    max_guests=row["max_guests"],
                    import_id=row["property_id"],
                )

                new_properties.append(prop)
                property_rows.append(row)

            Property.objects.bulk_create(
                new_properties,
                batch_size=batch_size,
            )

            images = []

            for prop, row in zip(new_properties, property_rows):
                for url in row["image_urls"]:
                    images.append(
                        PropertyImage(
                            property=prop,
                            image_url=url,
                        )
                    )

            PropertyImage.objects.bulk_create(
                images,
                batch_size=batch_size,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete: {len(new_properties)} new properties, "
                f"{len(images)} image URLs, "
                f"{len(validated) - len(new_properties)} existing "
                "properties skipped."
            )
        )
