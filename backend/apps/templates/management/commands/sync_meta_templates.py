from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.templates.services import sync_templates_from_meta


class Command(BaseCommand):
    help = "Sync WhatsApp message templates from Meta into the local Template model."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting Meta template sync..."))
        count = sync_templates_from_meta()
        self.stdout.write(self.style.SUCCESS(f"Synced {count} templates."))
