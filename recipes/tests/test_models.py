from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from recipes.models import Tag, Ingredient, Recipe

from recipes.models import recipe_image_file_path

def sample_user(**credentials):
    return get_user_model().objects.create_user(**credentials)


class ModelTests(TestCase):
    def setUp(self) -> None:
        self.CREDENTIALS = {
            "email": "admin@test.com",
            "password": "simple",
            "name": "admin",
        }

    def test_tag_str(self):
        tag = Tag.objects.create(
            user=sample_user(
                **self.CREDENTIALS
            ),
            name="Vegan",
        )
        self.assertEqual(str(tag), tag.name)


class IngredientModelTest(TestCase):
    def setUp(self) -> None:
        self.CREDENTIALS = {
            "email": "admin@test.com",
            "password": "simple",
            "name": "admin",
        }

    def test_ingredient_str(self):
        ingredient = Ingredient.objects.create(
            user=sample_user(**self.CREDENTIALS),
            name="Cucumber"
        )
        self.assertEqual(str(ingredient), ingredient.name)


class RecipeModelTests(TestCase):
    def setUp(self) -> None:
        self.CREDENTIALS = {
            "email": "admin@test.com",
            "password": "simple",
            "name": "admin",
        }

    def test_ingredient_str(self):
        recipe = Recipe.objects.create(
            user=sample_user(**self.CREDENTIALS),
            title="Steak",
            time_minutes=5,
            price=5.00
        )
        self.assertEqual(str(recipe), recipe.title)

    @patch("uuid.uuid4")
    def test_recipe_filename_uuid(self, mock):
        """Test if image saved in the correct location"""
        uuid = "sample-uuid"
        mock.return_value = uuid

        filepath = recipe_image_file_path(None, "image.jpg")
        exp_path = f'uploads/recipe/{uuid}.jpg'

        self.assertEqual(filepath, exp_path)
