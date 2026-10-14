from rest_framework import serializers

from rentals.models import Location


class LocationAutocompleteSerializer(serializers.ModelSerializer):
    distance = serializers.FloatField(read_only=True)

    class Meta:
        model = Location
        fields = ["id", "name", "distance"]