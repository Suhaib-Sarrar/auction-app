from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(tags=['notifications'])


@router.get('/notifications/me')
def my_notifications(db: Session = Depends(get_db),
                     current_user: models.User = Depends(get_current_user)):
    rows = (db.query(models.Notification)
            .filter(models.Notification.user_id == current_user.id)
            .order_by(models.Notification.id.desc())
            .limit(20)
            .all())
    return [{"id": n.id, "message": n.message, "is_read": n.is_read,
             "created_at": n.created_at} for n in rows]


@router.post('/notifications/{id}/read')
def mark_read(id: int, db: Session = Depends(get_db),
              current_user: models.User = Depends(get_current_user)):
    n = (db.query(models.Notification)
         .filter(models.Notification.id == id,
                 models.Notification.user_id == current_user.id)
         .first())
    if not n:
        raise HTTPException(status_code=404, detail="notification not found")
    n.is_read = True
    db.commit()
    return {"id": n.id, "is_read": n.is_read}