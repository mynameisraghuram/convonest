# backend/apps/contacts/services.py
from __future__ import annotations

from typing import Optional, Dict, Any
from django.utils import timezone

from .models import Contact


def touch_contact_from_inbound(
    *,
    phone: str,
    full_name: str = "",
    extra: Optional[Dict[str, Any]] = None,
    workspace=None,  # workspace is optional for backward compatibility
) -> Contact:
    """
    Upsert contact when an inbound message arrives.

    If workspace is provided, we scope by (workspace, phone).
    If workspace is None, fallback to phone only (legacy).
    """
    extra = extra or {}
    now = timezone.now()

    lookup = {"phone": phone}
    if workspace is not None:
        lookup["workspace"] = workspace

    contact, created = Contact.objects.get_or_create(
        **lookup,
        defaults={
            "full_name": full_name or "",
            "last_seen_at": now,
            "extra": extra,
        },
    )

    changed = False

    # Update name if we got a better one
    if full_name and contact.full_name != full_name:
        contact.full_name = full_name
        changed = True

    # Always touch last_seen_at
    contact.last_seen_at = now
    changed = True

    # Merge extra dict
    if isinstance(contact.extra, dict):
        merged = {**contact.extra, **extra}
    else:
        merged = extra

    if merged != contact.extra:
        contact.extra = merged
        changed = True

    if changed:
        contact.save()

    return contact
