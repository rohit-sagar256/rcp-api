
import pytest

from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from src.core.models import (Recipe, Tag, Ingredient)

from src.recipe.serializers import (
  RecipeSerializer,
  RecipeDetailSerializer

  )

User= get_user_model()


RECIPE_URL = reverse("recipe:recipe-list")


def detail_url(reciept_id):
  """ create and recipe detail url """
  return reverse("recipe:recipe-detail", args=[reciept_id])


def image_upload_url(recipe_id):
  return reverse("recipe:recipe-upload-image", args=[recipe_id])

@pytest.fixture(autouse=True)
def cleanup_media():
    yield
    from django.conf import settings
    import shutil
    if os.path.exists(settings.MEDIA_ROOT):
        shutil.rmtree(settings.MEDIA_ROOT)


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

# Recipes with tags
def test_create_recipe_with_new_tags(authenticated_user, user_cl):
  """ Test creating a recipe with new tags """
  payload = {
    "title": "Sample Recipe with Tags",
    "time_minutes": 30,
    "price": Decimal("5.99"),
    "tags": [{"name": "Vegan"}, {"name": "Dessert"}]
  }
  response = authenticated_user.post(RECIPE_URL, payload, format='json')

  assert response.status_code == status.HTTP_201_CREATED
  recipes = Recipe.objects.filter(user=user_cl)
  assert recipes.count() == 1
  recipe = recipes[0]
  assert recipe.tags.count() == 2
  for tag in payload['tags']:
    exists = recipe.tags.filter(
      name=tag['name'],
      user=user_cl
    ).exists()
    assert exists


def test_create_recipe_with_existing_tag(authenticated_user, user_cl):
  """ Test creating a recipe with existing tag """
  tag_indian = Tag.objects.create(user=user_cl, name="Indian")

  payload = {
    "title": "Sample Recipe with Existing Tag",
    "time_minutes": 30,
    "price": Decimal("5.99"),
    "tags": [{"name": "Indian"}, {"name": "Dessert"}]
  }
  response = authenticated_user.post(RECIPE_URL, payload, format='json')

  assert response.status_code == status.HTTP_201_CREATED
  recipes = Recipe.objects.filter(user=user_cl)
  assert recipes.count() == 1
  recipe = recipes[0]
  assert recipe.tags.count() == 2
  assert tag_indian in recipe.tags.all()
  for tag in payload['tags']:
    exists = recipe.tags.filter(
      name=tag['name'],
      user=user_cl
    ).exists()
    assert exists



def test_create_tag_on_update_recipe(authenticated_user, user_cl):
  """ Test creating a new tag when updating a recipe """
  recipe = create_recipe(user=user_cl)

  payload = {
    "tags": [{"name": "Lunch"}]
  }
  response = authenticated_user.patch(
    detail_url(recipe.id),
    payload,
    format='json'
  )
  assert response.status_code == status.HTTP_200_OK
  new_tag = Tag.objects.get(user=user_cl, name="Lunch")
  assert new_tag in recipe.tags.all()
  assert recipe.tags.count() == 1


def test_assigning_existing_tag_on_update_recipe(authenticated_user, user_cl):
  """ Test assigning an existing tag when updating a recipe """
  tag_breakfast = Tag.objects.create(user=user_cl, name="Breakfast")
  recipe = create_recipe(user=user_cl)
  recipe.tags.add(tag_breakfast)

  tag_lunch = Tag.objects.create(user=user_cl, name="Lunch")

  payload = {
    "tags": [{"name": "Lunch"}]
  }
  response = authenticated_user.patch(
    detail_url(recipe.id),
    payload,
    format='json'
  )
  assert response.status_code == status.HTTP_200_OK
  assert tag_lunch in recipe.tags.all()
  assert tag_breakfast not in recipe.tags.all()
  assert recipe.tags.count() == 1


def test_clear_recipe_tags(authenticated_user, user_cl):
  """ Test clearing a recipe's tags """
  tag = Tag.objects.create(user=user_cl, name="Dessert")
  recipe = create_recipe(user=user_cl)
  recipe.tags.add(tag)

  payload = {
    "tags": []
  }
  response = authenticated_user.patch(
    detail_url(recipe.id),
    payload,
    format='json'
  )
  assert response.status_code == status.HTTP_200_OK
  assert recipe.tags.count() == 0


# Recipes with ingredients

def test_create_recipe_with_new_ingredients(authenticated_user, user_cl):
  """ Test creating recipe with new ingredients """
  payload = {
    "title": "Sample Recipe with Tags",
    "time_minutes": 30,
    "price": Decimal("5.99"),
    "tags": [{"name": "Vegan"}, {"name": "Dessert"}],
    "ingredients" : [{"name":"chilli powder"}, {"name":"green chilli"}]
  }

  response = authenticated_user.post(RECIPE_URL, payload, format="json")

  assert response.status_code == status.HTTP_201_CREATED

  recipies = Recipe.objects.filter(user=user_cl)

  assert recipies.count() == 1

  recipe = recipies[0]

  assert recipe.ingredients.count() == 2

  for ingredient in payload["ingredients"]:
    exists = recipe.ingredients.filter(
      name=ingredient["name"],
      user = user_cl
    )

    assert exists


def test_create_recipe_with_existing_ingredients(authenticated_user, user_cl):
  """ Test creating a recipe with existing ingredients """
  ingredients_spices = Ingredient.objects.create(user=user_cl, name="Indian Masala")

  payload = {
    "title": "Sample Recipe with Existing Tag",
    "time_minutes": 30,
    "price": Decimal("5.99"),
    "ingredients": [{"name": "Indian Masala"}, {"name": "Cucumber"}],
  }
  response = authenticated_user.post(RECIPE_URL, payload, format='json')

  assert response.status_code == status.HTTP_201_CREATED
  recipes = Recipe.objects.filter(user=user_cl)
  assert recipes.count() == 1
  recipe = recipes[0]
  assert recipe.ingredients.count() == 2
  assert ingredients_spices in recipe.ingredients.all()
  for ingredient in payload['ingredients']:
    exists = recipe.ingredients.filter(
      name=ingredient['name'],
      user=user_cl
    ).exists()
    assert exists



def test_create_ingredient_on_update_recipe(authenticated_user, user_cl):
  """ Test creating a new ingredient when updating a recipe """
  recipe = create_recipe(user=user_cl)

  payload = {
    "ingredients": [{"name": "Red chilli"}]
  }
  response = authenticated_user.patch(
    detail_url(recipe.id),
    payload,
    format='json'
  )
  assert response.status_code == status.HTTP_200_OK
  new_ingredient = Ingredient.objects.get(user=user_cl, name="Red chilli")
  assert new_ingredient in recipe.ingredients.all()
  assert recipe.ingredients.count() == 1


def test_assigning_existing_ingredients_on_update_recipe(authenticated_user, user_cl):
  """ Test assigning an existing ingredients when updating a recipe """
  chilli_ingredient = Ingredient.objects.create(user=user_cl, name="Chilli")
  recipe = create_recipe(user=user_cl)
  recipe.ingredients.add(chilli_ingredient)

  apple_ingredient = Ingredient.objects.create(user=user_cl, name="Apple")

  payload = {
    "ingredients": [{"name": "Apple"}]
  }
  response = authenticated_user.patch(
    detail_url(recipe.id),
    payload,
    format='json'
  )
  assert response.status_code == status.HTTP_200_OK
  assert apple_ingredient in recipe.ingredients.all()
  assert chilli_ingredient not in recipe.ingredients.all()
  assert recipe.ingredients.count() == 1


def test_clear_recipe_ingredients(authenticated_user, user_cl):
  """ Test clearing a recipe's ingredients """
  ingredient = Ingredient.objects.create(user=user_cl, name="Saffron")
  recipe = create_recipe(user=user_cl)
  recipe.ingredients.add(ingredient)

  payload = {
    "ingredients": []
  }
  response = authenticated_user.patch(
    detail_url(recipe.id),
    payload,
    format='json'
  )
  assert response.status_code == status.HTTP_200_OK
  assert recipe.ingredients.count() == 0





def test_upload_image(authenticated_user, user_cl):
  """ Test uploading an image to a recipe """
  recipe = create_recipe(user=user_cl)
  url = image_upload_url(recipe.id)

  with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
    img = Image.new('RGB', (10,10))
    img.save(image_file, format="JPEG")
    image_file.seek(0)

    payload = {
      "image": image_file
    }

    response  = authenticated_user.post(url, payload, format="multipart")

  recipe.refresh_from_db()
  assert response.status_code == status.HTTP_200_OK
  assert "image" in response.data
  assert os.path.exists(recipe.image.path)



def test_upload_image_bad_request(authenticated_user, user_cl):
  """ Test uploading invalid image """
  recipe = create_recipe(user=user_cl)
  url = image_upload_url(recipe_id=recipe.id)

  payload = {"image":"notanimage"}

  res = authenticated_user.post(url, payload, format="multipart")
  assert res.status_code == status.HTTP_400_BAD_REQUEST




