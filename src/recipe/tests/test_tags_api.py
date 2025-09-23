""" Tests for the tags API."""
import pytest

from django.urls import reverse

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import (APIClient)

from src.core.models import Tag, Recipe
from src.recipe.serializers import TagSerializer

TAGS_URL = reverse("recipe:tag-list")

def detail_url(tag_id):
  """ Create and return a tag detail URL """
  return reverse("recipe:tag-detail", args=[tag_id])

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



def test_unauthenticated_user_retrive_tags(api_client):
  """ test that unauthenticated user cannot retrive tags """
  response = api_client.get(TAGS_URL)

  assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_retrive_tags(auth_client, user_cl):
  """ test retrive tags """

  Tag.objects.create(user=user_cl, name="Vegan")
  Tag.objects.create(user=user_cl, name="Dessert")

  response = auth_client.get(TAGS_URL)

  assert response.status_code == status.HTTP_200_OK
  tags = Tag.objects.filter(user=user_cl).order_by("-name")
  serializer = TagSerializer(tags, many=True)
  assert response.data == serializer.data

@pytest.mark.django_db
def test_tags_limited_to_user(auth_client,user_cl):
  """ test that tags returned are for the authenticated user """
  user2 = create_user(email="user2@example.com", password="testpass123")
  Tag.objects.create(user=user2, name="Fruity")

  tag = Tag.objects.create(user=user_cl, name="Comfort Food")
  response = auth_client.get(TAGS_URL)
  assert response.status_code == status.HTTP_200_OK

  assert len(response.data) == 1
  assert response.data[0]["name"] == tag.name
  assert response.data[0]["id"] == tag.id




def test_updte_tag(auth_client, user_cl):
  """ test updating a tag """
  tag = Tag.objects.create(user=user_cl, name="After Dinner")

  payload = {"name": "Dessert"}
  url = detail_url(tag.id)
  response = auth_client.patch(url, payload)

  assert response.status_code == status.HTTP_200_OK

  tag.refresh_from_db()

  assert tag.name == payload["name"]


def test_delete_tag(auth_client, user_cl):
  """ test deleting a tag """
  tag = Tag.objects.create(user=user_cl, name="Breakfast")

  url = detail_url(tag.id)
  response = auth_client.delete(url)

  assert response.status_code == status.HTTP_204_NO_CONTENT
  tags = Tag.objects.filter(user=user_cl)
  assert not tags.exists()
