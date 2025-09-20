from django.urls import include, path

from rest_framework.routers import DefaultRouter
from src.recipe import views



router = DefaultRouter()

router.register("recipes", views.RecipeViewSet)
app_name = "recipe"

urlpatterns = [
  path('', include(router.urls))
]

