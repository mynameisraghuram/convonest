# apps/whatsapp_accounts/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_send_test import send_test_message
from .views import (
    WhatsappBusinessAccountViewSet,
    WhatsappConnectionViewSet,
    WhatsappPhoneNumberViewSet,
    WhatsappContactViewSet,
    WhatsappConversationViewSet,
    WhatsappQrCodeViewSet,
)

router = DefaultRouter()
router.register(r"wabas", WhatsappBusinessAccountViewSet, basename="waba")
router.register(r"phone-numbers", WhatsappPhoneNumberViewSet, basename="phone-number")
router.register(r"contacts", WhatsappContactViewSet, basename="whatsapp-contact")
router.register(r"conversations", WhatsappConversationViewSet, basename="whatsapp-conversation")
router.register(r"qr-codes", WhatsappQrCodeViewSet, basename="whatsapp-qrcode")
router.register(r"connections", WhatsappConnectionViewSet, basename="whatsapp-connection")


urlpatterns = [
    # This will expose:
    # /api/whatsapp/wabas/
    # /api/whatsapp/phone-numbers/
    # /api/whatsapp/qr-codes/
    path("", include(router.urls)),
    path("", include("apps.whatsapp_accounts.urls_oauth")),
    path("send-test", send_test_message),
]
