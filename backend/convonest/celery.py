from __future__ import annotations

import os

from celery import Celery

# Default Django settings module for 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "convonest.settings")

app = Celery("convonest")

# Using a string means the worker doesn’t have to serialize
# the configuration object to child processes.
# - namespace="CELERY" tells Celery to look for CELERY_ keys in Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in all installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
