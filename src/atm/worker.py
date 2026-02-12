"""Celery worker configuration for async task processing."""

from celery import Celery

from src.atm.config import settings

celery_app = Celery(
    "atm_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,  # Results expire after 1 hour
)

celery_app.autodiscover_tasks(["src.atm.tasks"])
