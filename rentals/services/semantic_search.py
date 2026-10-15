from functools import lru_cache

from django.db.models import Case, IntegerField, Value, When
from pgvector.django import CosineDistance
from sentence_transformers import SentenceTransformer

from rentals.models import Location


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer(MODEL_NAME)


def search_locations(query, limit=5):
    query = query.strip()

    if len(query) < 2 or limit < 1:
        return Location.objects.none()

    # Prefix matching is more useful than vector similarity for partial names.
    prefix_matches = Location.objects.filter(
        name__istartswith=query
    ).annotate(
        relevance=Case(
            When(name__iexact=query, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by("relevance", "name")

    if prefix_matches.exists():
        return prefix_matches[:limit]

    model = get_embedding_model()
    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).tolist()

    return (
        Location.objects
        .filter(embedding__isnull=False)
        .annotate(
            distance=CosineDistance("embedding", query_embedding)
        )
        .order_by("distance", "name")[:limit]
    )
