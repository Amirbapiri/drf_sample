import uuid
import os

from django.db import models
from django.contrib.auth import get_user_model


class Tag(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=False,
        blank=False
    )

    def __str__(self):
        return self.name


def recipe_image_file_path(instance, filename):
    _, ext = filename.split(".")
    filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join("uploads/recipe/", filename)


class Recipe(models.Model):
    title = models.CharField(max_length=255, null=False, blank=False)
    user = models.ForeignKey(
        get_user_model(),
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)
    ingredients = models.ManyToManyField(
        "Ingredient"
    )
    tags = models.ManyToManyField(
        "Tag"
    )
    image = models.ImageField(upload_to=recipe_image_file_path, null=True)

    def __str__(self):
        return self.title
