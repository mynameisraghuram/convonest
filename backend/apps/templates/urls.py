
# backend/apps/templates/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ping, TemplateViewSet

router = DefaultRouter()
router.register(r"", TemplateViewSet, basename="templates")
urlpatterns = [
    path("ping/", ping),
    path("", include(router.urls)),
]

