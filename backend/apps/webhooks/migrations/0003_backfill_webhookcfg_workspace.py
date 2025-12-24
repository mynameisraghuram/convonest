
from django.db import migrations


def backfill(apps, schema_editor):
    WhatsappWebhookConfig = apps.get_model("webhooks", "WhatsappWebhookConfig")
    Workspace = apps.get_model("workspaces", "Workspace")

    # pick first workspace as fallback for legacy rows
    ws = Workspace.objects.order_by("created_at").first()
    if not ws:
        return

    WhatsappWebhookConfig.objects.filter(workspace__isnull=True).update(workspace=ws)


class Migration(migrations.Migration):
    dependencies = [
        ("webhooks", "0002_webhookeventlog_dedupe_key_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
