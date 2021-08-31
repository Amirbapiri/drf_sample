from django.urls import path, include

from rest_framework.routers import DefaultRouter

from api.accounts.views import (
    CreateUserView,
    CreateTokenView,
    ManageUserView,
)
from api.recipes.views import (
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
)

# Create endpoints for tags
router = DefaultRouter()
router.register("tags", TagViewSet)

# Create endpoints for ingredients
router.register("ingredients", IngredientViewSet)

# Create endpoints for recipes
router.register("recipes", RecipeViewSet)

urlpatterns = [
    # accounts
    path("create/", CreateUserView.as_view(), name="accounts_create"),
    path("token/", CreateTokenView.as_view(), name="accounts_token"),
    path("me/", ManageUserView.as_view(), name="accounts_me"),

    # recipes
    path("", include(router.urls))
]
