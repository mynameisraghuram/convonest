# backend/apps/messaging/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import InboxConversationViewSet, InboxMessageViewSet

router = DefaultRouter()
router.register("inbox/conversations", InboxConversationViewSet, basename="inbox-conversations")
router.register("inbox/messages", InboxMessageViewSet, basename="inbox-messages")

urlpatterns = [
    path("", include(router.urls)),
]
