
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from sentence_transformers import SentenceTransformer

from rentals.models import Location


class Command(BaseCommand):
    help = "Generate and store embeddings for location names."

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSIONS = 384

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=32,
            help="Number of location names to encode at once.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Regenerate embeddings for locations that already have them.",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]

        if batch_size < 1:
            raise CommandError("--batch-size must be greater than zero.")

        locations = Location.objects.all().order_by("id")

        if not options["force"]:
            locations = locations.filter(embedding__isnull=True)

        locations = list(locations)

        if not locations:
            self.stdout.write(
                self.style.WARNING("No locations need embeddings.")
            )
            return

        self.stdout.write(
            f"Loading model {self.MODEL_NAME}..."
        )

        try:
            model = SentenceTransformer(self.MODEL_NAME)

            names = [location.name for location in locations]

            embeddings = model.encode(
                names,
                batch_size=batch_size,
                show_progress_bar=True,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )

        except Exception as exc:
            raise CommandError(
                f"Could not generate embeddings: {exc}"
            ) from exc

        if embeddings.shape != (
            len(locations),
            self.EMBEDDING_DIMENSIONS,
        ):
            raise CommandError(
                f"Unexpected embedding shape: {embeddings.shape}"
            )

        with transaction.atomic():
            for location, embedding in zip(locations, embeddings):
                location.embedding = embedding.tolist()

            Location.objects.bulk_update(
                locations,
                ["embedding"],
                batch_size=batch_size,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Generated embeddings for {len(locations)} locations."
            )
        )
