import requests
from django.conf import settings

from .models import WhatsappConnection


class MetaGraph:
    @staticmethod
    def _api_base() -> str:
        if hasattr(settings, "META_API_BASE") and settings.META_API_BASE:
            return settings.META_API_BASE.rstrip("/")
        # fallback if you kept it inside WHATSAPP_META
        if hasattr(settings, "WHATSAPP_META") and settings.WHATSAPP_META.get("API_BASE"):
            return settings.WHATSAPP_META["API_BASE"].rstrip("/")
        raise RuntimeError("Missing META_API_BASE (or WHATSAPP_META['API_BASE']).")

    @staticmethod
    def _token_from_connection_or_settings(*, connection: WhatsappConnection = None, workspace_id: str = None) -> str:
        if connection and connection.access_token:
            return connection.access_token

        if workspace_id:
            conn = WhatsappConnection.objects.filter(workspace_id=workspace_id, is_active=True).first()
            if conn and conn.access_token:
                return conn.access_token

        # legacy fallback (temporary)
        if hasattr(settings, "META_ACCESS_TOKEN") and settings.META_ACCESS_TOKEN:
            return settings.META_ACCESS_TOKEN

        if hasattr(settings, "WHATSAPP_META") and settings.WHATSAPP_META.get("ACCESS_TOKEN"):
            return settings.WHATSAPP_META["ACCESS_TOKEN"]

        raise RuntimeError("No Meta access token available (no active connection, no settings token).")

    @staticmethod
    def _headers(token: str):
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def list_wabas(*, connection: WhatsappConnection = None, workspace_id: str = None):
        """
        GET /me/whatsapp_business_accounts
        """
        token = MetaGraph._token_from_connection_or_settings(connection=connection, workspace_id=workspace_id)
        url = f"{MetaGraph._api_base()}/me/whatsapp_business_accounts"
        r = requests.get(url, headers=MetaGraph._headers(token), timeout=30)
        r.raise_for_status()
        return r.json().get("data", [])

    @staticmethod
    def list_phone_numbers(waba_id: str, *, connection: WhatsappConnection = None, workspace_id: str = None):
        """
        GET /{waba_id}/phone_numbers
        """
        token = MetaGraph._token_from_connection_or_settings(connection=connection, workspace_id=workspace_id)
        url = f"{MetaGraph._api_base()}/{waba_id}/phone_numbers"
        r = requests.get(url, headers=MetaGraph._headers(token), timeout=30)
        r.raise_for_status()
        return r.json().get("data", [])
