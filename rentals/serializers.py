
from rest_framework import serializers

from rentals.models import Location, Property


class LocationAutocompleteQuerySerializer(serializers.Serializer):
    q = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        max_length=255,
    )
    limit = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=20,
    )


class PropertySearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        max_length=255,
    )
    radius_km = serializers.FloatField(
        required=False,
        default=20,
        min_value=0.001,
        max_value=500,
    )
    limit = serializers.IntegerField(
        required=False,
        default=20,
        min_value=1,
        max_value=100,
    )
    destination = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        trim_whitespace=True,
        max_length=255,
    )


class LocationAutocompleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name"]


class PropertySearchSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()
    semantic_distance = serializers.FloatField(read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "description",
            "address",
            "price_per_night",
            "max_guests",
            "amenities",
            "distance_km",
            "semantic_distance",
        ]

    def get_distance_km(self, obj):
        distance = getattr(obj, "distance", None)

        if distance is None:
            return None

        return round(distance.km, 2)
