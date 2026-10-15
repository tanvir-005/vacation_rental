from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from sentence_transformers import SentenceTransformer

from rentals.models import Property


class Command(BaseCommand):
    help = "Generate embeddings for property text and amenities."

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    DIMENSIONS = 384

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=32)
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        batch_size = options["batch_size"]

        if batch_size < 1:
            raise CommandError("--batch-size must be greater than zero.")

        queryset = Property.objects.order_by("id")

        if not options["force"]:
            queryset = queryset.filter(embedding__isnull=True)

        # Snapshot IDs so updates cannot shift queryset offsets.
        property_ids = list(queryset.values_list("id", flat=True))
        total = len(property_ids)

        if not total:
            self.stdout.write("No properties need embeddings.")
            return

        self.stdout.write(f"Generating embeddings for {total} properties...")

        try:
            model = SentenceTransformer(self.MODEL_NAME)

            for start in range(0, total, batch_size):
                batch_ids = property_ids[start:start + batch_size]
                batch = list(
                    Property.objects
                    .filter(id__in=batch_ids)
                    .select_related("location")
                    .order_by("id")
                )

                texts = [
                    " ".join([
                        f"Property: {prop.title}.",
                        f"Destination: {prop.location.name}.",
                        f"Address: {prop.address}.",
                        f"Description: {prop.description}.",
                        "Amenities: " + ", ".join(prop.amenities or []) + ".",
                    ])
                    for prop in batch
                ]

                vectors = model.encode(
                    texts,
                    batch_size=batch_size,
                    normalize_embeddings=True,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                )

                if vectors.shape != (len(batch), self.DIMENSIONS):
                    raise CommandError(
                        f"Unexpected embedding shape: {vectors.shape}"
                    )

                for prop, vector in zip(batch, vectors):
                    prop.embedding = vector.tolist()

                with transaction.atomic():
                    Property.objects.bulk_update(
                        batch,
                        ["embedding"],
                        batch_size=batch_size,
                    )

                self.stdout.write(
                    f"Processed {min(start + len(batch), total)}/{total}"
                )

        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(
                f"Could not generate property embeddings: {exc}"
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(f"Generated embeddings for {total} properties.")
        )
