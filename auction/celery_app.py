import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("auction", broker=REDIS_URL, include=["auction.tasks"])
