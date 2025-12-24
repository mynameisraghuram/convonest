from django.contrib.auth import get_user_model
from apps.workspaces.models import Workspace

User = get_user_model()

u = User.objects.filter(is_superuser=True).first()
if not u:
    raise Exception("No superuser found. Create one first.")

ws, created = Workspace.objects.get_or_create(
    name="Default Workspace",
    defaults={"owner": u},
)

print("Workspace ID:", ws.id)
print("Created:", created)
