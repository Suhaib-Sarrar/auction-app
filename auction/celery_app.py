import os

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("auction", broker=REDIS_URL, include=["auction.tasks"])

celery_app.conf.beat_schedule = {
    "close-expired-auctions": {
        "task": "auction.tasks.close_expired_auctions",
        "schedule": 60.0,          # كل 60 ثانية
    }
}
