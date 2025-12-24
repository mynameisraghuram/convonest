# backend/apps/contacts/services.py
from __future__ import annotations
from typing import Optional
from django.utils import timezone
from .models import Contact


def touch_contact_from_inbound(
    phone: str,
    *,
    full_name: str | None = None,
    language: str = "en",
    extra: dict | None = None,
) -> Contact:
    """
    Find or create a Contact for an inbound WhatsApp message.

    - Normalises phone (you can add a real normaliser later)
    - Updates last_seen_at
    - Optionally updates name/lang/extra
    """

    phone = phone.strip()

    defaults = {
        "last_seen_at": timezone.now(),
    }

    if full_name:
        defaults["full_name"] = full_name

    if language:
        defaults["language"] = language

    if extra:
        defaults["extra"] = {**extra}

    contact, _created = Contact.objects.update_or_create(
        phone=phone,
        defaults=defaults,
    )
    return contact
