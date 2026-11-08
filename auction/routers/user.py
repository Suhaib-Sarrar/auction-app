from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..security import Hash
from ..deps import require_permission
from ..deps import get_current_user

router = APIRouter(
    prefix="/user",
    tags=['user']
)


@router.get('/me')
def me(current_user: models.User = Depends(get_current_user)):
    return {"name": current_user.name, "email": current_user.email,
            "role": current_user.role.name}


@router.get('/', response_model=list[schemas.Show_user])
def show_user(db: Session = Depends(get_db),
              admin: models.User = Depends(require_permission("user:manage"))):
    user = db.query(models.User).all()
    return user


@router.post('/', response_model=schemas.Show_user, status_code=201)
def create_user(data: schemas.User, db: Session = Depends(get_db)):
    name = data.name.lower()

    if db.query(models.User).filter(models.User.name == name).first():
        raise HTTPException(status_code=400, detail="Name already taken")

    role = db.query(models.Role).filter(
        models.Role.name == data.role).first()
    if not role:
        role = models.Role(name=data.role)
        db.add(role)
        db.commit()
        db.refresh(role)

    new_user = models.User(
        name=name,
        email=data.email,
        password=Hash.bcrypt(data.password),
        role_id=role.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.delete('/{id}')
def destroy(id: int, db: Session = Depends(get_db),
            admin: models.User = Depends(require_permission("user:manage"))):
    user = db.query(models.User).filter(
        models.User.id == id)
    if not user.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"user with id {id} not found")
    user.delete(synchronize_session=False)
    db.commit()
    return 'Done'
