# backend/apps/webhooks/urls.py

# backend/apps/webhooks/urls.py

from django.urls import path
from .views_whatsapp import whatsapp_webhook

urlpatterns = [
    path("whatsapp/", whatsapp_webhook, name="whatsapp-webhook"),
]
