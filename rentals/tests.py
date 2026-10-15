
from unittest.mock import patch

from django.contrib.gis.geos import Point
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from rentals.models import Location, Property


class PropertySearchAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("property-search")

        self.location = Location.objects.create(
            name="Test Destination",
            point=Point(90.4125, 23.8103, srid=4326),
        )

        self.near_property = Property.objects.create(
            location=self.location,
            title="Near Property",
            description="A property near the destination",
            address="Near address",
            point=Point(90.4130, 23.8105, srid=4326),
            price_per_night=2000,
            max_guests=2,
            amenities=["WiFi"],
            embedding=[0.1] * 384,
        )

        self.far_property = Property.objects.create(
            location=self.location,
            title="Far Property",
            description="A property far from the destination",
            address="Far address",
            point=Point(91.0, 24.0, srid=4326),
            price_per_night=3000,
            max_guests=4,
            amenities=["Parking"],
            embedding=[0.2] * 384,
        )

    @patch("rentals.views.get_embedding_model")
    def _mock_model(self, mock_get_model):
        model = mock_get_model.return_value
        model.encode.return_value = type(
            "EmbeddingResult",
            (),
            {"tolist": lambda self: [0.1] * 384},
        )()
        return mock_get_model

    def test_missing_query_returns_400(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 400)
        self.assertIn("q", response.data)

    def test_blank_query_returns_400(self):
        response = self.client.get(self.url, {"q": "   "})

        self.assertEqual(response.status_code, 400)

    def test_invalid_radius_returns_400(self):
        response = self.client.get(
            self.url,
            {"q": "property", "radius_km": 501},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("radius_km", response.data)

    def test_invalid_limit_returns_400(self):
        response = self.client.get(
            self.url,
            {"q": "property", "limit": 0},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("limit", response.data)

    @patch("rentals.views.get_embedding_model")
    def test_semantic_search_returns_results_without_distance(
        self,
        mock_get_model,
    ):
        mock_get_model.return_value.encode.return_value.tolist.return_value = (
            [0.1] * 384
        )

        response = self.client.get(
            self.url,
            {"q": "quiet property"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["query"], "quiet property")
        self.assertIsNone(response.data["destination"])
        self.assertIsNone(response.data["radius_km"])
        self.assertTrue(response.data["results"])

        for result in response.data["results"]:
            self.assertIn("semantic_distance", result)
            self.assertIsNone(result["distance_km"])

    @patch("rentals.views.search_locations")
    @patch("rentals.views.get_embedding_model")
    def test_geographic_filter_excludes_far_property(
        self,
        mock_get_model,
        mock_search_locations,
    ):
        mock_search_locations.return_value = [self.location]
        mock_get_model.return_value.encode.return_value.tolist.return_value = (
            [0.1] * 384
        )

        response = self.client.get(
            self.url,
            {
                "q": "property",
                "destination": "Test Destination",
                "radius_km": 5,
            },
        )

        self.assertEqual(response.status_code, 200)

        result_ids = {
            result["id"] for result in response.data["results"]
        }

        self.assertIn(self.near_property.id, result_ids)
        self.assertNotIn(self.far_property.id, result_ids)

        for result in response.data["results"]:
            self.assertIsNotNone(result["distance_km"])

    @patch("rentals.views.search_locations")
    @patch("rentals.views.get_embedding_model")
    def test_unknown_destination_returns_empty_results(
        self,
        mock_get_model,
        mock_search_locations,
    ):
        mock_search_locations.return_value = []
        mock_get_model.return_value.encode.return_value.tolist.return_value = (
            [0.1] * 384
        )

        response = self.client.get(
            self.url,
            {
                "q": "property",
                "destination": "Unknown destination",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])
        self.assertIsNone(response.data["selected_location"])

    @patch("rentals.views.get_embedding_model")
    def test_limit_restricts_result_count(self, mock_get_model):
        mock_get_model.return_value.encode.return_value.tolist.return_value = (
            [0.1] * 384
        )

        response = self.client.get(
            self.url,
            {"q": "property", "limit": 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    @patch("rentals.views.get_embedding_model")
    def test_results_are_ordered_by_semantic_distance(
        self,
        mock_get_model,
    ):
        mock_get_model.return_value.encode.return_value.tolist.return_value = (
            [0.1] * 384
        )

        response = self.client.get(
            self.url,
            {"q": "property"},
        )

        self.assertEqual(response.status_code, 200)

        distances = [
            result["semantic_distance"]
            for result in response.data["results"]
        ]

        self.assertEqual(distances, sorted(distances))
