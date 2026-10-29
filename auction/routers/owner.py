from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db


router = APIRouter(
    prefix="/owner",
    tags=['owner']
)


@router.get('/')
def shwo_oner(db: Session = Depends(get_db)):
    owner = db.query(models.Owner).all()
    return owner


@router.post('/', response_model=schemas.Shwo_Owner)
def create_owner(request: schemas.Owner, db: Session = Depends(get_db)):
    new_owner = models.Owner(
        owner_name=request.owner_name, owner_email=request.owner_email,
        owner_password=request.owner_password
    )
    db.add(new_owner)
    db.commit()
    db.refresh(new_owner)
    return new_owner


@router.delete('/{id}')
def destroy(id: int, db: Session = Depends(get_db)):
    owner = db.query(models.Owner).filter(models.Owner.owner_id == id)
    if not owner.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"owner with id {id} not found")
    owner.delete(synchronize_session=False)
    db.commit()
    return 'Done'
