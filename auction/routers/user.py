from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..security import Hash


router = APIRouter(
    prefix="/user",
    tags=['user']
)


@router.get('/', response_model=list[schemas.Show_user])
def show_user(db: Session = Depends(get_db)):
    user = db.query(models.User).all()
    return user


@router.post('/', response_model=schemas.Show_user)
def create_user(data: schemas.User, db: Session = Depends(get_db)):
    role = db.query(models.Role).filter(
        models.Role.name == data.role).first()
    if not role:
        role = models.Role(name=data.role)
        db.add(role)
        db.commit()
        db.refresh(role)
    new_user = models.User(
        name=data.name.lower(), email=data.email,
        password=Hash.bcrypt(data.password),
        role_id=role.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.delete('/{id}')
def destroy(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.id == id)
    if not user.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"user with id {id} not found")
    user.delete(synchronize_session=False)
    db.commit()
    return 'Done'
