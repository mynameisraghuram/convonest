from django.urls import path
from .views import csrf

urlpatterns = [
    path("csrf/", csrf),
]
