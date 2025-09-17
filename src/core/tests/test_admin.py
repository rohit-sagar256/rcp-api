"""Tests for django admin modification"""
import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse


User = get_user_model()

@pytest.fixture
def admin_user(client, db):
  return User.objects.create_superuser(email='admin@example.com', password='testpass123')


@pytest.fixture
def user(db):
  return User.objects.create_user(
    email='user@example.com',
    password='user@123'
  )



@pytest.fixture
def admin_client(client, admin_user):
  client.force_login(admin_user)
  return client




@pytest.mark.django_db
def test_users_list(admin_client, user):
  url = reverse("admin:core_user_changelist")
  response = admin_client.get(url)

  assert response.status_code == 200
  assert user.email in response.content.decode()


@pytest.mark.django_db
def test_edit_user_page(admin_client, user):
  url = reverse("admin:core_user_change", args=[user.id])
  response = admin_client.get(url)

  assert response.status_code == 200



@pytest.mark.django_db
def test_create_user_page(admin_client, user):
  url = reverse("admin:core_user_add")
  response = admin_client.get(url)
  assert response.status_code == 200








# @pytest.mark.django_db
# def test_

