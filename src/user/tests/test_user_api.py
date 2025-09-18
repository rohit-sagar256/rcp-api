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
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")

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

  def test_create_token_for_user(self,api_client):
    """ Test generates token for valid credentials """
    user_details = {
      "name": "Test Name",
      "email": "test@example.com",
      "password": "test-user-password123"
    }

    create_user(**user_details)

    payload = {
      "email": user_details["email"],
      "password": user_details["password"]
    }

    response = api_client.post(TOKEN_URL, payload)

    assert "token" in response.data
    assert response.status_code == status.HTTP_200_OK


  def test_create_token_bad_credentials(self, api_client):
    """ Test return error if credentials invalid """
    create_user(email="test@example.com", password="goodpass")

    payload = {"email": "test@example.com", "password": "badpass"}

    response = api_client.post(TOKEN_URL, payload)

    assert "token" not in response.data
    assert response.status_code == status.HTTP_400_BAD_REQUEST

  def test_create_token_blank_password(self, api_client):
    """ Test return error if password is blank """
    create_user(email="test@example.com", password="goodpass")

    payload = {"email": "test@example.com", "password": ""}

    response = api_client.post(TOKEN_URL, payload)

    assert "token" not in response.data
    assert response.status_code == status.HTTP_400_BAD_REQUEST

  def test_retrieve_user_unathorized(self, api_client):
    """ Test authentication is required for users """
    response = api_client.get(ME_URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED






@pytest.fixture
def private_user(db):
    return create_user(
        email="test@example.com",
        password="pass123",
        name="Test Private"
    )

@pytest.fixture
def authenticated_user(private_user):
  client = APIClient()
  client.force_authenticate(user=private_user)
  return client



@pytest.mark.django_db
class TestPrivateUser:
  """ Test api request that requires authentication """

  def test_retrieve_profile_success(self, private_user, authenticated_user):
    """ Test retrieving profile for logged in user """
    response = authenticated_user.get(ME_URL)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == private_user.name
    assert response.data["email"] == private_user.email

  def test_post_me_not_allowed(self,authenticated_user):
    response = authenticated_user.post(ME_URL, {})
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

  def test_update_user_profile(self, private_user, authenticated_user):
    """ Test updating the user profile for the authenticated """
    payload = {"name": "updated name", "password":"newpassword"}

    response = authenticated_user.patch(ME_URL, payload)
    private_user.refresh_from_db()
    assert private_user.name == payload["name"]
    assert private_user.check_password(payload["password"])

    assert response.status_code  == status.HTTP_200_OK

