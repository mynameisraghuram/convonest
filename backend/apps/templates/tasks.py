from __future__ import annotations

import logging
from celery import shared_task

from .services import sync_templates_from_meta

logger = logging.getLogger(__name__)


@shared_task
def sync_templates_from_meta_task() -> int:
    logger.info("Starting template sync from Meta...")
    count = sync_templates_from_meta()
    logger.info("Finished template sync from Meta: %s templates", count)
    return count
