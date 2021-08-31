import os
import tempfile

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient
from PIL import Image

from recipes.models import Recipe, Tag, Ingredient
from api.recipes.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse("api_v1:recipe-list")
RECIPES_DETAIL_URL = "api_v1:recipe-detail"


def image_upload_url(recipe_id):
    """
    Return URL for recipe image upload
    """
    return reverse("api_v1:recipe-upload-image", args=[recipe_id])


def sample_tag(user, name="sample name"):
    return Tag.objects.create(
        user=user,
        name=name
    )


def sample_ingredient(user, name="sample ingredient"):
    return Ingredient.objects.create(
        user=user,
        name=name,
    )


def sample_recipe(user, **payload):
    defaults = {
        "title": "sample recipe",
        "time_minutes": 5,
        "price": 5.00,
    }
    defaults.update(**payload)

    return Recipe.objects.create(
        user=user,
        **defaults,
    )


def get_detail_url(id):
    return reverse(RECIPES_DETAIL_URL, args=[id])


class PublicRecipeAPITests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_authentication_required(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@gmail.com",
            "test_simple",
        )

        self.client.force_authenticate(self.user)

    def test_retrieve_list_of_recipes(self):
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all()
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_list_of_recipes_limited_to_user(self):
        temp_user = get_user_model().objects.create_user(
            "temp_user@gmail.com",
            "temp_simple",
        )

        sample_recipe(user=temp_user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = get_detail_url(recipe.id)

        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        payload = {
            "title": "some recipe",
            "time_minutes": 30,
            "price": 10.00,
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data.get("id"))
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        def create_some_tags():
            tag1 = sample_tag(user=self.user)
            tag2 = sample_tag(user=self.user)
            return [tag1.id, tag2.id]

        payload = {
            "title": "recipe with tags",
            "time_minutes": 60,
            "price": 20.00,
            "tags": create_some_tags(),
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data.get("id"))
        tags_of_recipe = recipe.tags.all()

        self.assertEqual(tags_of_recipe.count(), 2)

        for key in payload:
            if not key == "tags":
                self.assertEqual(
                    payload[key],
                    getattr(recipe, key)
                )

        for tag in payload["tags"]:
            self.assertIn(tag, list(tags_of_recipe.values_list("id", flat=True)))

    def test_create_recipe_with_ingredients(self):
        def create_some_ingredients():
            ingredient1 = sample_ingredient(self.user, name="Ingredient 1")
            ingredient2 = sample_ingredient(self.user, name="Ingredient 2")
            return [ingredient1.id, ingredient2.id]

        payload = {
            "title": "recipe with ingredient",
            "time_minutes": 30,
            "price": 99.00,
            "ingredients": create_some_ingredients(),
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data.get("id"))
        ingredients_of_recipe = recipe.ingredients.all()

        self.assertEqual(ingredients_of_recipe.count(), 2)

        for key in payload:
            if not key == "ingredients":
                self.assertEqual(
                    payload[key],
                    getattr(recipe, key)
                )

        for ingredient in payload["ingredients"]:
            self.assertIn(ingredient, list(ingredients_of_recipe.values_list("id", flat=True)))

    def test_partial_update_recipe(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        new_tag = sample_tag(user=self.user, name="Django recipe")

        payload = {
            "title": "update payload recipe",
            "tags": [new_tag.id]
        }

        url = get_detail_url(recipe.id)
        self.client.patch(url, payload)

        # Refreshing database to be able get the latest update
        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload["title"])
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        payload = {
            "title": "full update",
            "time_minutes": 20,
            "price": 99.00,
        }

        url = get_detail_url(recipe.id)
        self.client.put(url, payload)

        # Refreshing database to be able get the latest update
        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.time_minutes, payload["time_minutes"])
        self.assertEqual(recipe.price, payload["price"])

        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)


class RecipeImageUploadTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "newuser@gmail.com",
            "simple_password"
        )

        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)

            res = self.client.post(url, {'image': ntf}, format="multipart")
        self.recipe.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_bad_request(self):
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'noimage'}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipes_by_tags(self):
        r1 = sample_recipe(self.user, title="R1")
        r2 = sample_recipe(self.user, title="R2")

        tag1 = sample_tag(self.user, name="tag1")
        tag2 = sample_tag(self.user, name="tag2")
        r1.tags.add(tag1)
        r2.tags.add(tag2)

        r3 = sample_recipe(self.user, title="Not included")

        res = self.client.get(
            RECIPES_URL,
            {'tags': f'{tag1.id}, {tag2.id}'}
        )

        serializer1 = RecipeSerializer(r1)
        serializer2 = RecipeSerializer(r2)
        serializer3 = RecipeSerializer(r3)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_by_ingredients(self):
        r1 = sample_recipe(self.user, title="R1")
        r2 = sample_recipe(self.user, title="R2")
        ingredient1 = sample_ingredient(self.user, name="ingredient1")
        ingredient2 = sample_ingredient(self.user, name="ingredient2")

        r1.ingredients.add(ingredient1)
        r2.ingredients.add(ingredient2)

        r3 = sample_recipe(self.user, title="Not included")

        serializer1 = RecipeSerializer(r1)
        serializer2 = RecipeSerializer(r2)
        serializer3 = RecipeSerializer(r3)

        res = self.client.get(
            RECIPES_URL,
            {"ingredients": f'{ingredient1.id}, {ingredient2.id}'}
        )

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)
