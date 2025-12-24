from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.contacts.models import Contact
from apps.messaging.models import (
    MessageLog,
    MessageDirection,
    MessageStatus,
    MessageType,
)


class Command(BaseCommand):
    help = "Seed inbox with a test inbound WhatsApp message"

    def handle(self, *args, **options):
        phone = "+919701621666"

        contact, _ = Contact.objects.get_or_create(
            phone=phone,
            defaults={"full_name": "Ram"},
        )

        msg = MessageLog.objects.create(
            direction=MessageDirection.INBOUND,
            msg_type=MessageType.TEXT,
            status=MessageStatus.RECEIVED,
            contact=contact,
            contact_phone=contact.phone,
            body_text="Hello from WhatsApp 👋 (seeded)",
            received_at=timezone.now(),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded inbox message for {contact.phone} (message id={msg.id})"
            )
        )
