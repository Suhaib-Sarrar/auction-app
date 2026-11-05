import os
import smtplib
from email.message import EmailMessage

from . import models
from .celery_app import celery_app
from .database import SessionLocal

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
MAIL_FROM = os.getenv("MAIL_FROM", "auction@example.com")


def send_email(to: str, subject: str, body: str):
    msg = EmailMessage()
    msg["From"] = MAIL_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.send_message(msg)


@celery_app.task(autoretry_for=(OSError,), retry_backoff=True, max_retries=3)
def send_new_bid_email(bid_id: int):
    db = SessionLocal()
    try:
        bid = db.get(models.Bid, bid_id)
        if bid is None:
            return
        owner = bid.product.owner
        send_email(
            owner.email,
            f"New bid on {bid.product.title}",
            f"Hi {owner.name},\n\n"
            f"{bid.bidder.name} placed a bid of {bid.amount} "
            f"on your product '{bid.product.title}'.\n",
        )
    finally:
        db.close()


@celery_app.task(autoretry_for=(OSError,), retry_backoff=True, max_retries=3)
def send_bid_accepted_email(bid_id: int):
    db = SessionLocal()
    try:
        bid = db.get(models.Bid, bid_id)
        if bid is None:
            return
        bidder = bid.bidder
        send_email(
            bidder.email,
            f"Your bid was accepted: {bid.product.title}",
            f"Hi {bidder.name},\n\n"
            f"The owner accepted your bid of {bid.amount} "
            f"on '{bid.product.title}'. Congratulations!\n",
        )
    finally:
        db.close()
