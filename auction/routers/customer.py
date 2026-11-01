from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..hashing import Hash


router = APIRouter(
    prefix="/customer",
    tags=['customer']
)


@router.get('/')
def shwo_customer(db: Session = Depends(get_db)):
    customer = db.query(models.Customer).all()
    return customer


@router.post('/', response_model=schemas.Show_customer)
def create_owner(request: schemas.Customer, db: Session = Depends(get_db)):
    new_customer = models.Customer(
        customer_name=request.customer_name, customer_email=request.customer_email,
        customer_password=Hash.bcrypt(request.customer_password)
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


@router.delete('/{id}')
def destroy(id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(
        models.Customer.customer_id == id)
    if not customer.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"customer with id {id} not found")
    customer.delete(synchronize_session=False)
    db.commit()
    return 'Done'
