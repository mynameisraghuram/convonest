from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model that adds created_at and updated_at timestamps.
    Use this for almost all domain models.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
