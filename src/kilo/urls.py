from django.urls import path

from .views import kilohomepage

urlpatterns = [
    path("kilo-homepage",kilohomepage, name="kilo.homepage")
]

