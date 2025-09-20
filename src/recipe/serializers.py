from rest_framework import serializers
from src.core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):

  class Meta:
    model=Recipe
    fields = ["id", "title",  "time_minutes", "price", "link"]
    read_only_fields= ["id"]
    


