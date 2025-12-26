
# backend/apps/whatsapp_accounts/urls_oauth.py
from django.urls import path
from .views_oauth import oauth_start, oauth_callback

urlpatterns = [
    path("oauth/start", oauth_start),
    path("oauth/callback", oauth_callback),
]
