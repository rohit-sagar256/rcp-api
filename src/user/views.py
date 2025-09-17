""" views for the user api """

from rest_framework import generics

from src.user.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
  serializer_class = UserSerializer


