import pytest
from django.urls import resolve, reverse
from django.contrib.auth import get_user_model

User = get_user_model()




@pytest.mark.django_db
def test_kilo_home_page(client):
  url = reverse("kilo.homepage")
  response = client.get(url)
  assert response.status_code == 200
  assert "Hello" in response.content.decode()
