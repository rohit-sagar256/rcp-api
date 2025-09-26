"""
Tests from models
"""
import os
from decimal import Decimal

import pytest

from unittest.mock import patch

from django.contrib.auth import get_user_model

from src.core import models

User = get_user_model()


@pytest.mark.django_db
def test_create_user_with_email_successfull():
  email = "test2@example.com"
  password = "testpass123"
  user = get_user_model().objects.create_user(
    email=email,
    password=password
  )

  assert user.email == email
  assert user.check_password(password)


@pytest.mark.django_db
def test_new_user_email_normalize():
    sample_email = [
      ["test1@EXAMPLE.com", "test1@example.com"],
      ["Test2@example.com", "Test2@example.com"],
      ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
      ["test4@example.COM", "test4@example.com"],
    ]

    for email, expected in sample_email:
      user = User.objects.create_user(email, 'sample123')
      assert user.email == expected


@pytest.mark.django_db
def test_new_user_without_email_raises_error():
  with pytest.raises(ValueError):
    User.objects.create_user(email=None, password='test!1243')



@pytest.mark.django_db
def test_create_super_user():
  user = User.objects.create_superuser(
    email="test1@example.com",
    password="test123"
  )

  assert user.is_superuser
  assert user.is_staff

@pytest.mark.django_db
def test_create_recipe():
    user = User.objects.create_user(
        email="test@example.com",
        password="testpass123"
    )

    recipe = models.Recipe.objects.create(
        user=user,
        title="test",
        description="Sample Recipe Test",
        time_minutes=5,
        price=Decimal("3.50")
    )

    assert str(recipe) == recipe.title




@pytest.mark.django_db
def test_create_tag():
  user = User.objects.create_user(
    email="testtaguser@example.com",
    password="testpass123"
  )

  tag = models.Tag.objects.create(
    user=user,
    name="Vegan"
  )
  assert str(tag) == tag.name


@pytest.mark.django_db
def test_create_ingredient():
  user = User.objects.create_user(
    email="testingredientuser@gmail.com",
    password="testpass123"
  )

  ingredient = models.Ingredient.objects.create(
    user=user,
    name="Cucumber"
  )
  assert str(ingredient) == ingredient.name


@patch('src.core.models.uuid.uuid4')
def test_recipe_file_name_uuid(mock_uuid):
  """ Test generating image path """

  uuid = "test-uuid"
  mock_uuid.return_value = uuid

  file_path = models.recipe_image_file_path(None, 'example.jpg')
  expected_path = os.path.join("uploads", "recipe", f"{uuid}.jpg")
  assert file_path == expected_path
