from collections import Counter

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from sentence_transformers import SentenceTransformer

from rentals.models import Location, Property


class Command(BaseCommand):
    help = "Generate embeddings from destination and property information."

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSIONS = 384

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=32)
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        batch_size = options["batch_size"]

        if batch_size < 1:
            raise CommandError("--batch-size must be greater than zero.")

        locations = Location.objects.order_by("id")

        if not options["force"]:
            locations = locations.filter(embedding__isnull=True)

        locations = list(locations)

        if not locations:
            self.stdout.write("No locations need embeddings.")
            return

        profiles = []

        for location in locations:
            properties = Property.objects.filter(location=location)

            amenity_counts = Counter()
            titles = []
            neighborhoods = set()

            for title, address, amenities in properties.values_list(
                "title", "address", "amenities"
            ).iterator():
                if title:
                    titles.append(title.strip())

                if address:
                    parts = [part.strip() for part in address.split(",")]
                    if len(parts) > 2:
                        neighborhoods.add(parts[0])

                amenity_counts.update(
                    item.strip()
                    for item in (amenities or [])
                    if isinstance(item, str) and item.strip()
                )

            profile = (
                f"Destination: {location.name}. "
                f"Neighborhoods: {', '.join(sorted(neighborhoods))}. "
                f"Vacation rental property types: "
                f"{', '.join(sorted(set(titles)))}. "
                f"Common amenities: "
                f"{', '.join(name for name, _ in amenity_counts.most_common(20))}."
            )

            profiles.append(profile)

        self.stdout.write(f"Loading {self.MODEL_NAME}...")

        try:
            model = SentenceTransformer(self.MODEL_NAME)
            embeddings = model.encode(
                profiles,
                batch_size=batch_size,
                show_progress_bar=True,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
        except Exception as exc:
            raise CommandError(
                f"Could not generate embeddings: {exc}"
            ) from exc

        if embeddings.shape != (len(locations), self.EMBEDDING_DIMENSIONS):
            raise CommandError(f"Unexpected embedding shape: {embeddings.shape}")

        with transaction.atomic():
            for location, embedding in zip(locations, embeddings):
                location.embedding = embedding.tolist()

            Location.objects.bulk_update(
                locations, ["embedding"], batch_size=batch_size
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Generated property-informed embeddings for {len(locations)} locations."
            )
        )
