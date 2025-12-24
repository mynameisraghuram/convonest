# backend/apps/messaging/urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import InboxConversationViewSet, InboxMessageViewSet
from .webhook_views import whatsapp_webhook_verify, whatsapp_webhook_receive

router = DefaultRouter()
router.register("inbox/conversations", InboxConversationViewSet, basename="inbox-conversations")
router.register("inbox/messages", InboxMessageViewSet, basename="inbox-messages")

urlpatterns = router.urls + [
    # WhatsApp Webhook (Meta)
    path("webhook/whatsapp/", whatsapp_webhook_verify, name="wa-webhook-verify"),
    path("webhook/whatsapp/receive/", whatsapp_webhook_receive, name="wa-webhook-receive"),
]
