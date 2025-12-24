from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Tuple, Optional

import requests
from django.conf import settings

from .models import (
    Template,
    TemplateButtonConfig,
    TemplateCategory,
    TemplateStatus,
    TemplateAuthType,
    TemplateSource,
    TemplateButtonType,
)

logger = logging.getLogger(__name__)


class MetaWhatsAppError(RuntimeError):
    pass


def _get_meta_client_config() -> Tuple[str, str, str]:
    waba_id = getattr(settings, "META_WABA_ID", None) or os.getenv("META_WABA_ID")
    access_token = getattr(settings, "META_ACCESS_TOKEN", None) or os.getenv("META_ACCESS_TOKEN")
    base_url = getattr(settings, "META_API_BASE", None) or os.getenv("META_API_BASE", "https://graph.facebook.com/v21.0")

    if not waba_id or not access_token:
        raise MetaWhatsAppError("META_WABA_ID or META_ACCESS_TOKEN not configured")

    return str(waba_id), str(access_token), str(base_url).rstrip("/")


def fetch_templates_from_meta() -> List[Dict[str, Any]]:
    """
    GET /{WABA_ID}/message_templates
    Basic pagination via cursors.after
    """
    waba_id, access_token, base_url = _get_meta_client_config()

    url = f"{base_url}/{waba_id}/message_templates"
    params = {
        "access_token": access_token,
        "limit": 100,
        # fields improves usefulness (Meta may ignore unknown fields)
        "fields": "id,name,language,category,sub_category,status,components,namespace,rejected_reason,quality_score,messaging_limit_tier,disabled",
    }

    templates: List[Dict[str, Any]] = []

    while True:
        resp = requests.get(url, params=params, timeout=30)
        try:
            resp.raise_for_status()
        except Exception:
            raise MetaWhatsAppError(f"Meta fetch templates failed: {resp.text}")

        data = resp.json() if resp.content else {}
        templates.extend(data.get("data", []))

        paging = data.get("paging", {}) or {}
        cursors = paging.get("cursors", {}) or {}
        after = cursors.get("after")
        if after:
            params["after"] = after
        else:
            break

    logger.info("Fetched %s templates from Meta", len(templates))
    return templates


def create_template_on_meta(*, name: str, language: str, category: str, components: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    POST /{WABA_ID}/message_templates
    """
    waba_id, access_token, base_url = _get_meta_client_config()
    url = f"{base_url}/{waba_id}/message_templates"

    payload = {
        "name": name,
        "language": language,
        "category": category,
        "components": components,
        "access_token": access_token,
    }

    resp = requests.post(url, json=payload, timeout=30)
    if resp.status_code >= 400:
        raise MetaWhatsAppError(f"Meta create template failed: {resp.text}")

    return resp.json() if resp.content else {}


def _map_meta_category(meta_category: Optional[str]) -> str:
    meta_category = (meta_category or "").upper()
    if meta_category == "MARKETING":
        return TemplateCategory.MARKETING
    if meta_category == "UTILITY":
        return TemplateCategory.UTILITY
    if meta_category == "AUTHENTICATION":
        return TemplateCategory.AUTHENTICATION
    return TemplateCategory.UTILITY


def _detect_auth_type(components: List[Dict[str, Any]]) -> str:
    for comp in components or []:
        if comp.get("type") == "BUTTONS":
            for btn in comp.get("buttons", []):
                btn_type = (btn.get("type") or "").upper()
                if btn_type in ("OTP", "COPY_CODE"):
                    return TemplateAuthType.COPY_CODE
    return TemplateAuthType.NONE


def _extract_body_text(components: List[Dict[str, Any]]) -> str:
    for comp in components or []:
        if comp.get("type") == "BODY":
            return comp.get("text") or ""
    return ""


def _normalize_components_for_meta(stored_components: Any) -> List[Dict[str, Any]]:
    """
    Your Template.components may be:
      - a Meta array: [ {...}, {...} ]
      - a dict wrapper: {"components":[...]} or {"value":[...]}
      - something else
    We normalize to a Meta components array.
    """
    if isinstance(stored_components, list):
        return stored_components
    if isinstance(stored_components, dict):
        if isinstance(stored_components.get("components"), list):
            return stored_components["components"]
        if isinstance(stored_components.get("value"), list):
            return stored_components["value"]
    return []


def _upsert_buttons(template: Template, components: List[Dict[str, Any]]) -> None:
    TemplateButtonConfig.objects.filter(template=template).delete()

    idx = 0
    for comp in components or []:
        if comp.get("type") != "BUTTONS":
            continue

        for btn in comp.get("buttons", []):
            idx += 1
            btn_type_raw = (btn.get("type") or "").upper()

            if btn_type_raw in ("QUICK_REPLY", "QUICK_REPLY_BUTTON"):
                btn_type = TemplateButtonType.QUICK_REPLY
            elif btn_type_raw in ("URL", "URL_BUTTON", "CALL_TO_ACTION"):
                btn_type = TemplateButtonType.URL
            elif btn_type_raw in ("PHONE_NUMBER", "PHONE"):
                btn_type = TemplateButtonType.PHONE
            else:
                btn_type = TemplateButtonType.OTHER

            TemplateButtonConfig.objects.create(
                template=template,
                index=idx,
                button_type=btn_type,
                text=(btn.get("text") or "")[:191],
                url=btn.get("url"),
                phone_number=btn.get("phone_number"),
                payload=btn.get("payload"),
                extra=btn or {},
            )


def sync_templates_from_meta() -> int:
    raw_templates = fetch_templates_from_meta()
    count = 0

    status_choices = {c[0] for c in TemplateStatus.choices}

    for item in raw_templates:
        name = item.get("name") or ""
        language = item.get("language") or "en"
        category = _map_meta_category(item.get("category"))

        components = item.get("components", []) or []
        body_text = _extract_body_text(components)

        status_raw = (item.get("status") or "PENDING").upper()
        status = status_raw if status_raw in status_choices else TemplateStatus.PENDING

        auth_type = _detect_auth_type(components)
        variable_count = body_text.count("{{")

        quality = item.get("quality_score") or {}
        quality_rating = quality.get("current_score") or item.get("quality_rating")

        tpl, _created = Template.objects.update_or_create(
            name=name,
            language=language,
            defaults={
                "external_id": item.get("id"),
                "namespace": item.get("namespace"),
                "category": category,
                "subtype": item.get("sub_category") or None,
                "auth_type": auth_type,
                "body_text": body_text,
                "components": components,
                "variable_count": variable_count,
                "quality_rating": quality_rating,
                "messaging_limit_tier": item.get("messaging_limit_tier"),
                "status": status,
                "is_paused": bool(item.get("disabled")),
                "rejection_reason": item.get("rejected_reason") or item.get("rejection_reason"),
                "meta_raw": item,
                "source": TemplateSource.META_SYNC,
            },
        )

        _upsert_buttons(tpl, components)
        count += 1

    logger.info("Synced %s templates into local DB", count)
    return count


def refresh_one_template_status_from_meta(template: Template) -> Template:
    """
    Lightweight "sync just one" by name.
    """
    items = fetch_templates_from_meta()
    found = None
    for it in items:
        if it.get("name") == template.name and (it.get("language") or "en") == template.language:
            found = it
            break

    if not found:
        return template

    status_choices = {c[0] for c in TemplateStatus.choices}
    status_raw = (found.get("status") or template.status).upper()
    template.status = status_raw if status_raw in status_choices else template.status

    template.external_id = found.get("id") or template.external_id
    template.rejection_reason = found.get("rejected_reason") or found.get("rejection_reason")

    quality = found.get("quality_score") or {}
    template.quality_rating = quality.get("current_score") or template.quality_rating

    template.messaging_limit_tier = found.get("messaging_limit_tier") or template.messaging_limit_tier
    template.is_paused = bool(found.get("disabled"))

    template.meta_raw = found
    template.source = TemplateSource.META_SYNC
    template.save()

    _upsert_buttons(template, found.get("components", []) or [])
    return template


def submit_local_template_to_meta(template: Template) -> Template:
    """
    Submit local DRAFT template to Meta and set status -> PENDING
    """
    meta_components = _normalize_components_for_meta(template.components)
    if not meta_components:
        raise MetaWhatsAppError("Template.components has no valid Meta components array to submit.")

    resp = create_template_on_meta(
        name=template.name,
        language=template.language,
        category=template.category,
        components=meta_components,
    )

    template.external_id = resp.get("id") or template.external_id
    template.status = TemplateStatus.PENDING
    template.source = TemplateSource.LOCAL
    template.rejection_reason = None
    template.save()

    return template
