from django.core.management.base import BaseCommand
from apps.workspaces.models import Workspace
from apps.whatsapp_accounts.models import (
    WhatsappBusinessAccount,
    WhatsappPhoneNumber,
    WhatsappConnection,
)


class Command(BaseCommand):
    help = "Bootstrap WhatsApp WABA + phone number + workspace connection"

    def handle(self, *args, **options):
        workspace = Workspace.objects.first()
        if not workspace:
            self.stdout.write(
                self.style.ERROR("❌ No workspace found. Run bootstrap_workspace first.")
            )
            return

        # ---- WABA ----
        waba, _ = WhatsappBusinessAccount.objects.get_or_create(
            id="WABA_TEST_1",
            defaults={
                "name": "Test WABA",
                "is_connected": True,
            },
        )

        # ---- Phone Number ----
        phone, _ = WhatsappPhoneNumber.objects.get_or_create(
            id="PHONE_NUMBER_ID_TEST_1",
            defaults={
                "waba": waba,
                "e164_number": "+919999999999",
                "display_name": "Test WhatsApp Number",
                "registered": True,
            },
        )

        # ---- Connection (ROUTING KEY) ----
        conn, created = WhatsappConnection.objects.get_or_create(
            workspace=workspace,
            waba=waba,
            phone_number=phone,
            defaults={
                "access_token": "TEST_ACCESS_TOKEN",
                "verify_token": "TEST_VERIFY_TOKEN",
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ WhatsApp connection created for workspace {workspace.id}"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️ WhatsApp connection already exists"
                )
            )
