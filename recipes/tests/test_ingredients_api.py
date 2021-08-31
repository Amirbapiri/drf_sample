from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from recipes.models import Ingredient, Recipe
from api.recipes.serializers import TagSerializer, IngredientSerializer

INGREDIENTS_URL = reverse("api_v1:ingredient-list")


class PublicIngredientsAPITest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_login_required(self):
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "simple",
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        Ingredient.objects.create(
            user=self.user,
            name="Kale"
        )
        Ingredient.objects.create(
            user=self.user,
            name="Salt"
        )

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_ingredient_limited_to_user(self):
        temp_user = get_user_model().objects.create_user(
            "tempuser@gmail.com",
            "simple_test",
        )

        Ingredient.objects.create(
            user=temp_user,
            name="Vinegar",
        )
        ingredient = Ingredient.objects.create(
            user=self.user,
            name="Tumeric",
        )

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)

    def test_add_ingredient(self):
        payload = {
            "name": "Ingredient 2",
        }
        res = self.client.post(INGREDIENTS_URL, payload)

        exists = Ingredient.objects.filter(
            name=payload["name"],
            user=self.user,
        ).exists()

        self.assertTrue(exists)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_ingredient_invalid_payload(self):
        payload = {
            "name": ""
        }
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipes(self):
        ingredient1 = Ingredient.objects.create(
            user=self.user,
            name="Apples"
        )
        ingredient2 = Ingredient.objects.create(
            user=self.user,
            name="Turkey"
        )

        recipe = Recipe.objects.create(
            title="recip1",
            time_minutes=5,
            price=10.00,
            user=self.user
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredients_assigned_unique(self):
        ingredient1 = Ingredient.objects.create(user=self.user, name="ingredient")
        Ingredient.objects.create(user=self.user, name="ingredient 2")

        recipe1 = Recipe.objects.create(
            title="recipe1",
            time_minutes=5,
            price=10.00,
            user=self.user
        )
        recipe1.ingredients.add(ingredient1)

        recipe2 = Recipe.objects.create(
            title="recipe2",
            time_minutes=10,
            price=210.00,
            user=self.user
        )
        recipe2.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
