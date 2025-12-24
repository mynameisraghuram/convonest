import secrets
from typing import Any, Dict, Optional, Tuple

import requests
from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner


def _api_base() -> str:
    return settings.META_API_BASE.rstrip("/")


def _signer() -> TimestampSigner:
    return TimestampSigner(salt=settings.META_OAUTH_STATE_SALT)


def build_oauth_state(*, workspace_id: str) -> str:
    nonce = secrets.token_urlsafe(16)
    raw = f"ws={workspace_id}&nonce={nonce}"
    return _signer().sign(raw)


def parse_oauth_state(state: str, *, max_age_seconds: int = 600) -> Dict[str, str]:
    try:
        raw = _signer().unsign(state, max_age=max_age_seconds)
    except SignatureExpired as e:
        raise ValueError("OAuth state expired. Please try again.") from e
    except BadSignature as e:
        raise ValueError("Invalid OAuth state.") from e

    parts = dict(p.split("=", 1) for p in raw.split("&") if "=" in p)
    ws = parts.get("ws")
    if not ws:
        raise ValueError("Invalid OAuth state payload.")
    return {"workspace_id": ws}


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
    # Long-lived user token exchange :contentReference[oaicite:2]{index=2}
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


def graph_get(path: str, token: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{_api_base()}/{path.lstrip('/')}"
    p = {"access_token": token}
    if params:
        p.update(params)
    r = requests.get(url, params=p, timeout=30)
    r.raise_for_status()
    return r.json()


def graph_post(path: str, token: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{_api_base()}/{path.lstrip('/')}"
    payload = data or {}
    payload["access_token"] = token
    r = requests.post(url, data=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def discover_waba_and_phone(token: str) -> Tuple[str, str, Dict[str, Any]]:
    # MVP: choose first business → first WABA → first phone number.
    businesses = graph_get("/me/businesses", token).get("data", []) or []
    if not businesses:
        raise ValueError("No Business found. Ensure Business Manager access.")

    business_id = businesses[0]["id"]

    wabas = graph_get(f"/{business_id}/owned_whatsapp_business_accounts", token).get("data", []) or []
    if not wabas:
        raise ValueError("No WABA found under this Business.")

    waba_id = wabas[0]["id"]

    phones = graph_get(f"/{waba_id}/phone_numbers", token).get("data", []) or []
    if not phones:
        raise ValueError("No phone numbers found under this WABA.")

    phone_number_id = phones[0]["id"]

    return waba_id, phone_number_id, {
        "business_id": business_id,
        "wabas_preview": wabas[:10],
        "phones_preview": phones[:10],
    }


def subscribe_app_to_waba_webhooks(token: str, waba_id: str) -> Dict[str, Any]:
    # POST /{waba_id}/subscribed_apps :contentReference[oaicite:3]{index=3}
    return graph_post(f"/{waba_id}/subscribed_apps", token, data={})
