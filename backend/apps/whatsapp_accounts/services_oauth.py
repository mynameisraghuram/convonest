# backend/apps/whatsapp_accounts/services_oauth.py

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, List

import requests
from django.conf import settings
from django.core import signing


# -----------------------------
# OAuth state helpers (SIGNED)
# -----------------------------
def build_oauth_state(*, workspace_id: str) -> str:
    """
    Signed state to prevent tampering (SaaS-safe).
    Uses META_OAUTH_STATE_SALT from settings.
    """
    payload = {"workspace_id": str(workspace_id)}
    return signing.dumps(payload, salt=settings.META_OAUTH_STATE_SALT)


def parse_oauth_state(state: str) -> dict:
    """
    Verify state signature and expire it after 10 minutes.
    """
    return signing.loads(state, salt=settings.META_OAUTH_STATE_SALT, max_age=600)


# -----------------------------
# Basics
# -----------------------------
def _api_base() -> str:
    return (settings.META_API_BASE or "").rstrip("/")


def build_login_url(*, state: str) -> str:
    scope = ",".join([s.strip() for s in settings.META_OAUTH_SCOPES if s.strip()])
    return (
        f"https://www.facebook.com/{settings.META_GRAPH_VERSION}/dialog/oauth"
        f"?client_id={settings.META_APP_ID}"
        f"&redirect_uri={settings.META_REDIRECT_URI}"
        f"&state={state}"
        f"&response_type=code"
        f"&scope={scope}"
    )


# -----------------------------
# Token exchange
# -----------------------------
def exchange_code_for_short_token(code: str) -> Dict[str, Any]:
    url = f"{_api_base()}/oauth/access_token"
    params = {
        "client_id": settings.META_APP_ID,
        "client_secret": settings.META_APP_SECRET,
        "redirect_uri": settings.META_REDIRECT_URI,
        "code": code,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def exchange_short_for_long_token(short_token: str) -> Dict[str, Any]:
    """
    Exchange short-lived user token for a long-lived user token.
    """
    url = f"{_api_base()}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": settings.META_APP_ID,
        "client_secret": settings.META_APP_SECRET,
        "fb_exchange_token": short_token,
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


# -----------------------------
# Graph helpers
# -----------------------------
def graph_get(path: str, token: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    GET wrapper for Graph API using access_token query param.
    """
    url = f"{_api_base()}/{path.lstrip('/')}"
    p = {"access_token": token}
    if params:
        p.update(params)
    r = requests.get(url, params=p, timeout=30)
    r.raise_for_status()
    return r.json()


def graph_post(path: str, token: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    POST wrapper for Graph API using access_token in form-data.
    """
    url = f"{_api_base()}/{path.lstrip('/')}"
    payload = data or {}
    payload["access_token"] = token
    r = requests.post(url, data=payload, timeout=30)
    r.raise_for_status()
    return r.json()


# -----------------------------
# WABA + Phone discovery
# -----------------------------
def discover_waba_and_phone(token: str) -> Tuple[str, str, Dict[str, Any]]:
    """
    Discover a WABA_ID and PHONE_NUMBER_ID accessible by this token.

    Returns:
      (waba_id, phone_number_id, meta_discovery)

    meta_discovery includes:
      - chosen_waba: dict
      - chosen_phone: dict
      - raw discovery responses for debugging

    Strategy:
      1) Try /me/whatsapp_business_accounts (works for some setups)
      2) Fallback: /me/businesses -> /{business_id}/owned_whatsapp_business_accounts
      3) Then /{waba_id}/phone_numbers
    """
    meta: Dict[str, Any] = {}
    wabas: List[Dict[str, Any]] = []

    # 1) Direct edge attempt
    try:
        resp = graph_get(
            "/me/whatsapp_business_accounts",
            token,
            params={"fields": "id,name,account_review_status,currency,timezone_id"},
        )
        meta["me_whatsapp_business_accounts"] = resp
        wabas = resp.get("data") or []
    except Exception as e:
        meta["me_whatsapp_business_accounts_error"] = str(e)

    # 2) Fallback via businesses
    if not wabas:
        businesses_resp = graph_get("/me/businesses", token, params={"fields": "id,name"})
        meta["me_businesses"] = businesses_resp

        businesses = businesses_resp.get("data") or []
        if not businesses:
            raise ValueError(
                "No Business found for this token. Ensure the Meta user has Business Manager access "
                "and the app has required permissions."
            )

        meta["owned_whatsapp_business_accounts"] = {}
        meta["owned_whatsapp_business_accounts_error"] = {}

        for b in businesses:
            business_id = b.get("id")
            if not business_id:
                continue
            try:
                owned_resp = graph_get(
                    f"/{business_id}/owned_whatsapp_business_accounts",
                    token,
                    params={"fields": "id,name,account_review_status,currency,timezone_id"},
                )
                meta["owned_whatsapp_business_accounts"][business_id] = owned_resp
                wabas.extend(owned_resp.get("data") or [])
            except Exception as e:
                meta["owned_whatsapp_business_accounts_error"][business_id] = str(e)

    if not wabas:
        raise ValueError(
            "No WABA found for this token. Make sure the Meta user has access to a WhatsApp Business Account "
            "and permissions include whatsapp_business_management."
        )

    # MVP: pick the first WABA
    chosen_waba = wabas[0]
    waba_id = chosen_waba.get("id")
    if not waba_id:
        raise ValueError(f"Discovered WABA without id: {chosen_waba}")

    meta["chosen_waba"] = chosen_waba

    # Fetch phone numbers under the WABA
    phones_resp = graph_get(
        f"/{waba_id}/phone_numbers",
        token,
        params={
            "fields": (
                "id,display_phone_number,verified_name,code_verification_status,quality_rating,"
                "name_status,status,messaging_limit_tier,is_official_business_account"
            )
        },
    )
    meta["waba_phone_numbers"] = phones_resp

    phones = phones_resp.get("data") or []
    if not phones:
        raise ValueError(
            f"No phone numbers found under WABA {waba_id}. Add/finish WhatsApp phone number setup in WhatsApp Manager."
        )

    chosen_phone = phones[0]
    phone_number_id = chosen_phone.get("id")
    if not phone_number_id:
        raise ValueError(f"Discovered phone number without id: {chosen_phone}")

    meta["chosen_phone"] = chosen_phone

    return waba_id, phone_number_id, meta


def subscribe_app_to_waba_webhooks(token: str, waba_id: str) -> Dict[str, Any]:
    """
    POST /{waba_id}/subscribed_apps
    """
    return graph_post(f"/{waba_id}/subscribed_apps", token, data={})
