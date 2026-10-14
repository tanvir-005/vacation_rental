from functools import lru_cache

from pgvector.django import CosineDistance
from sentence_transformers import SentenceTransformer

from rentals.models import Location


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    return SentenceTransformer(MODEL_NAME)


def search_locations(query, limit=5):
    query = query.strip()

    if not query:
        return Location.objects.none()

    model = get_embedding_model()

    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ).tolist()

    return (
        Location.objects
        .exclude(embedding__isnull=True)
        .annotate(
            distance=CosineDistance("embedding", query_embedding)
        )
        .order_by("distance", "name")[:limit]
    )