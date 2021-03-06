from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from recipes.models import Tag, Recipe
from api.recipes.serializers import TagSerializer

TAGS_URL = reverse("api_v1:tag-list")


class PublicTagsAPITests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_authentication_required(self):
        """Test authentication is required to be able to retrieve tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "simple",
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        Tag.objects.create(
            user=self.user,
            name="Vegan",
        )
        Tag.objects.create(
            user=self.user,
            name="Dessert",
        )

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_authenticated_user(self):
        Tag.objects.create(
            user=self.user,
            name="Vegan",
        )
        Tag.objects.create(
            user=self.user,
            name="Dessert",
        )

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.filter(user=self.user)
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_tag_successful(self):
        payload = {
            "name": "test tag",
            "user": self.user,
        }
        self.client.post(TAGS_URL, payload)
        exists = Tag.objects.filter(
            user=self.user,
            name=payload["name"],
        ).exists()

        self.assertTrue(exists)

    def test_create_tag_invalid_payload(self):
        payload = {
            "name": "",
            "user": ""
        }

        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_recipes(self):
        tag1 = Tag.objects.create(user=self.user, name="Breakfast")
        tag2 = Tag.objects.create(user=self.user, name="Lunch")

        recipe = Recipe.objects.create(
            title="Recipe1",
            time_minutes=5,
            price=20.00,
            user=self.user,
        )
        recipe.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)
        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_tags_assigned_unique(self):
        tag = Tag.objects.create(user=self.user, name="Breakfast")
        Tag.objects.create(user=self.user, name="Lunch")
        recipe1 = Recipe.objects.create(
            title="Recipe",
            time_minutes=5,
            price=30.00,
            user=self.user,
        )
        recipe1.tags.add(tag)
        recipe2 = Recipe.objects.create(
            title="Recipe2",
            time_minutes=10,
            price=40.00,
            user=self.user
        )
        recipe2.tags.add(tag)

        res = self.client.get(TAGS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)