
import pytest

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from src.core.models import Recipe

from src.recipe.serializers import RecipeSerializer

User= get_user_model()


RECIPE_URL = reverse("recipe:recipe-list")



@pytest.fixture
def user_cl(db):
  return User.objects.create_user(
    email="user@example.com",
    password="testpass123"
  )


@pytest.fixture
def api_client():
  return APIClient()

@pytest.fixture
def authenticated_user(user_cl):
  client = APIClient()
  client.force_authenticate(user_cl)
  return client

def create_recipe(user,**params):
  defaults = {
    "title" : "Sample Recipe title",
    "time_minutes":22,
    "price": Decimal("5.24"),
    "description": "Sample description",
    "link": "https://example.com/recipe.pdf"
  }

  defaults.update(params)

  recipe = Recipe.objects.create(user=user, **defaults)
  return recipe


def test_unauthenticated_user_failed_getting_recipe(api_client):
  response= api_client.get(RECIPE_URL)
  assert response.status_code == status.HTTP_401_UNAUTHORIZED



def test_authenticated_user_retrive_recipe_list(authenticated_user, user_cl):

  create_recipe(user=user_cl)
  create_recipe(user=user_cl)

  response = authenticated_user.get(RECIPE_URL)

  recipes = Recipe.objects.all().order_by("-id")

  serializer = RecipeSerializer(recipes, many=True)
  assert response.status_code == status.HTTP_200_OK
  assert response.data == serializer.data


def test_recipe_list_limited_to_user(authenticated_user, user_cl):
  other_user= User.objects.create_user(
    "otheruser@example.com",
    "password123"
  )
  create_recipe(user=user_cl)
  create_recipe(user=other_user)


  response = authenticated_user.get(RECIPE_URL)

  recipies = Recipe.objects.filter(user=user_cl)
  serializer=RecipeSerializer(recipies, many=True)

  assert response.status_code == status.HTTP_200_OK
  assert response.data ==serializer.data






