from decimal import Decimal

import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from src.core.models import (Ingredient, Recipe)
from src.recipe.serializers import IngredientSerializer


INGREDIENT_URL = reverse("recipe:ingredient-list")

def detail_url(ingredient_id):
  """ Create and return an ingredient detail url """
  return reverse("recipe:ingredient-detail", args=[ingredient_id])

def create_user(email="user@example.com",password="testpass123"):
  return get_user_model().objects.create_user(email=email,password=password)


@pytest.fixture
def user_cl(db):
  return create_user()

@pytest.fixture
def api_client():
  return APIClient()


@pytest.fixture
def auth_client(user_cl):
  client = APIClient()
  client.force_authenticate(user_cl)
  return client



def test_unauthenticated_user_retrieve_ingredients(api_client):
  """ test that unauthenticated user cannot retrive ingredients """
  response = api_client.get(INGREDIENT_URL)
  assert response.status_code == status.HTTP_401_UNAUTHORIZED



@pytest.mark.django_db
def test_retriev_ingredients(auth_client, user_cl):
  """ test retrieve ingredients """
  Ingredient.objects.create(user=user_cl, name="Cucumber")
  Ingredient.objects.create(user=user_cl, name="Pulse")

  response = auth_client.get(INGREDIENT_URL)

  assert response.status_code == status.HTTP_200_OK
  ingredients = Ingredient.objects.filter(user=user_cl).order_by("-name")
  serializer = IngredientSerializer(ingredients, many=True)
  assert response.data == serializer.data



@pytest.mark.django_db
def test_ingredients_limited_to_user(auth_client, user_cl):
  """ test that ingredients returned are for the authenticated user """
  user2 = create_user(email="user2@example.com", password="testpass123")

  Ingredient.objects.create(user=user2, name="Red chilli powder")

  ingredient = Ingredient.objects.create(user=user_cl, name="Green chilli")

  response = auth_client.get(INGREDIENT_URL)

  assert response.status_code == status.HTTP_200_OK

  assert len(response.data) == 1
  assert response.data[0]["name"] == ingredient.name
  assert response.data[0]["id"] == ingredient.id



def test_update_ingredients(auth_client, user_cl):
  """ test updating ingredients """
  ingredient = Ingredient.objects.create(user=user_cl, name="Kashmiri mirch")
  payload = {"name" : "kashmiri mirch updated"}

  url =detail_url(ingredient_id=ingredient.id)

  response = auth_client.patch(url, payload)

  assert response.status_code == status.HTTP_200_OK

  ingredient.refresh_from_db()

  assert payload["name"] == response.data["name"]



def test_delete_ingredient(auth_client, user_cl):
  """ test deleting ingredient """
  ingredient = Ingredient.objects.create(user=user_cl, name="Chilli powder")

  url = detail_url(ingredient.id)

  response = auth_client.delete(url)

  assert response.status_code == status.HTTP_204_NO_CONTENT

  ingredients = Ingredient.objects.filter(user=user_cl)

  assert not ingredients.exists()



def test_filter_ingredients_assigned_to_recipies(auth_client, user_cl):
  """ Test listing ingredients by those assigned to recipes """

  ingredient1 = Ingredient.objects.create(user=user_cl, name="Masala")
  ingredient2 = Ingredient.objects.create(user=user_cl, name="Saffron")

  recipe = Recipe.objects.create(
    title="Apple pie",
    time_minutes=4,
    price=Decimal("4.50"),
    user =user_cl
  )

  recipe.ingredients.add(ingredient1)

  response = auth_client.get(INGREDIENT_URL, {"assigned_only" : 1})

  s1 = IngredientSerializer(ingredient1)
  s2 = IngredientSerializer(ingredient2)

  assert s1.data in response.data
  assert s2.data not in response.data

def test_filtered_ingredients_unique(auth_client, user_cl):
  """ Test filtered ingredients returns a unique list """

  ingredient = Ingredient.objects.create(user=user_cl, name="Masala")

  Ingredient.objects.create(user=user_cl, name="Saffron")

  recipe1 = Recipe.objects.create(
    title="Apple pie",
    time_minutes=4,
    price=Decimal("4.50"),
    user =user_cl
  )

  recipe2 = Recipe.objects.create(
    title="Eggs curry",
    time_minutes=10,
    price=Decimal('9.02'),
    user=user_cl
  )

  recipe1.ingredients.add(ingredient)
  recipe2.ingredients.add(ingredient)

  response = auth_client.get(INGREDIENT_URL, {"assigned_only" : 1})

  assert len(response.data) == 1
