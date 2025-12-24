


from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.workspaces.models import Workspace

class Command(BaseCommand):
    help = "Create a default workspace"

    def handle(self, *args, **options):
        User = get_user_model()
        u = User.objects.filter(is_superuser=True).first()
        if not u:
            self.stderr.write("No superuser found.")
            return

        ws, created = Workspace.objects.get_or_create(
            name="Default Workspace",
            defaults={"owner": u},
        )

        self.stdout.write(f"Workspace ID: {ws.id}")
        self.stdout.write(f"Created: {created}")
