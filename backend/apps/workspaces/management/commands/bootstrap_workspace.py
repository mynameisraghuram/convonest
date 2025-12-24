from django.core.management.base import BaseCommand
from apps.workspaces.models import Workspace


class Command(BaseCommand):
    help = "Create default workspace if none exists"

    def handle(self, *args, **options):
        ws, created = Workspace.objects.get_or_create(
            name="Default Workspace"
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Workspace created: {ws.id} ({ws.name})"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ Workspace already exists: {ws.id} ({ws.name})"
                )
            )
