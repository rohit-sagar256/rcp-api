
import pytest

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from src.core.models import Recipe

from src.recipe.serializers import (
  RecipeSerializer,
  RecipeDetailSerializer

  )

User= get_user_model()


RECIPE_URL = reverse("recipe:recipe-list")


def detail_url(reciept_id):
  """ create and recipe detail url """
  return reverse("recipe:recipe-detail", args=[reciept_id])

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





def test_get_recipe_detail(authenticated_user, user_cl):
  """ Test get recipe detail """
  recipe = create_recipe(user=user_cl)

  url = detail_url(reciept_id=recipe.id)

  response = authenticated_user.get(url)

  serializer = RecipeDetailSerializer(recipe)

  assert response.status_code == status.HTTP_200_OK

  assert serializer.data == response.data

def test_create_recipe(authenticated_user, user_cl):
  """ Test creating a recipe """

  payload = {
    "title": "Sample Recipe",
    "time_minutes": 30,
    "price": Decimal("5.99"),
    "description": "Sample description",
    "link": "https://example.com/recipe.pdf"
  }

  response = authenticated_user.post(RECIPE_URL, payload)

  assert response.status_code == status.HTTP_201_CREATED

  recipe = Recipe.objects.get(id=response.data["id"])

  for key in payload.keys():
    assert payload[key] == getattr(recipe, key)

  assert recipe.user == user_cl

def test_partial_update_recipe(authenticated_user, user_cl):
  original_link = "https://example.com/recipe.pdf"
  updated_link = "https://example.com/new-recipe.pdf"
  recipe = create_recipe(
    user=user_cl,
    title="Sample recipe title",
    link=original_link,
    description="Sample description"
  )

  response = authenticated_user.patch(
    detail_url(recipe.id),
    {"title": "New recipe title", "link": updated_link}
  )

  assert response.status_code == status.HTTP_200_OK
  recipe.refresh_from_db()
  assert recipe.title == "New recipe title"
  assert recipe.link == updated_link
  assert recipe.user == user_cl


def test_full_update_recipe(authenticated_user, user_cl):
  recipe = create_recipe(
    user=user_cl,
    title="Sample recipe title",
    link="https://example.com/recipe.pdf",
    description="Sample description"
  )
  payload = {
    "title": "New recipe title",
    "link": "https://example.com/new-recipe.pdf",
    "description": "New sample description",
    "time_minutes": 10,
    "price": Decimal("2.50")
  }
  response = authenticated_user.put(
    detail_url(recipe.id),
    payload
  )
  assert response.status_code == status.HTTP_200_OK
  recipe.refresh_from_db()
  for key,value in payload.items():
    assert value == getattr(recipe, key)


def test_changing_user_on_update_recipe(authenticated_user, user_cl):
  """ Test changing the recipe user when updating the recipe """
  new_user = User.objects.create_user(
    email="testnewuser@gmail.com",
    password="testpass123",
  )

  recipe = create_recipe(user=user_cl)

  response = authenticated_user.patch(
    detail_url(recipe.id),
    {"user": new_user.id}
  )

  assert response.status_code == status.HTTP_200_OK
  recipe.refresh_from_db()
  assert recipe.user == user_cl
  assert recipe.user != new_user


def test_delete_recipe(authenticated_user, user_cl):
  """ Test deleting a recipe successful """
  recipe = create_recipe(user=user_cl)

  response = authenticated_user.delete(
    detail_url(recipe.id)
  )

  assert response.status_code == status.HTTP_204_NO_CONTENT
  assert not Recipe.objects.filter(id=recipe.id).exists()


def test_delete_other_users_recipe_error(authenticated_user, user_cl):
  """ Test trying to delete another user's recipe gives error """
  new_user = User.objects.create_user(
    email="newusertest@gmail.com",
    password="testpass123",
  )
  recipe = create_recipe(user=new_user)
  response = authenticated_user.delete(
    detail_url(recipe.id)
  )
  assert response.status_code == status.HTTP_404_NOT_FOUND
  assert Recipe.objects.filter(id=recipe.id).exists()
