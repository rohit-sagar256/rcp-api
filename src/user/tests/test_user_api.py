"""
Test for the user API
"""
import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework  import status
from faker import Faker

User = get_user_model()

CREATE_USER_URL = reverse("user:create")

faker=Faker()


def create_user(**params):
  """create and return new user
  """
  return User.objects.create_user(**params)

@pytest.fixture
def api_client():
  return APIClient()

# Public User Tests

@pytest.mark.django_db
class TestPublicUserApi:
  def test_create_user_success(self, api_client):
    payload = {
      "email": faker.email(domain="example.com"),
      "password": "testpass123",
      "name": faker.name()
    }

    response = api_client.post(CREATE_USER_URL, payload)

    assert response.status_code == status.HTTP_201_CREATED
    user = User.objects.get(email=payload["email"])

    assert user.check_password(payload["password"])

    assert 'password' not in response.data


  def test_user_with_email_exists_error(self, api_client):
    """ Test error return if user with email exists """

    payload = {
      "email": faker.email(domain="example.com"),
      "password": "testpass123",
      "name": "Test Name"
    }

    create_user(**payload)

    response = api_client.post(CREATE_USER_URL, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


  def test_password_too_short(self, api_client):
    """ Test an error is returned if password less than 5 chars """

    payload = {
      "email": faker.email(domain="example.com"),
      "password": "test",
      "name": "Test Name"
    }

    response = api_client.post(CREATE_USER_URL, payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    user_exists = User.objects.filter(
      email=payload["email"]
    ).exists()

    assert user_exists == False










