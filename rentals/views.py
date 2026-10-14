from rest_framework.response import Response
from rest_framework.views import APIView

from rentals.serializers import LocationAutocompleteSerializer
from rentals.services.semantic_search import search_locations


class LocationAutocompleteView(APIView):
    def get(self, request):
        query = request.query_params.get("q", "").strip()

        try:
            limit = int(request.query_params.get("limit", 5))
        except ValueError:
            return Response(
                {"error": "INVALID_LIMIT", "message": "Limit must be an integer."},
                status=400,
            )

        if not 1 <= limit <= 20:
            return Response(
                {"error": "INVALID_LIMIT", "message": "Limit must be between 1 and 20."},
                status=400,
            )

        if not query:
            return Response(
                {"error": "MISSING_QUERY", "message": "Provide a search query using q."},
                status=400,
            )

        locations = search_locations(query, limit=limit)

        serializer = LocationAutocompleteSerializer(
            locations,
            many=True,
        )

        return Response({
            "query": query,
            "results": serializer.data,
        })