from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..deps import require_owner, get_current_user
from datetime import datetime, timezone
from ..models import ProductStatus


router = APIRouter(
    prefix="/products",
    tags=['products']
)


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(dt):
    if dt is not None and dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def check_can_open(end_time):
    if end_time is None or end_time <= utcnow():
        raise HTTPException(status_code=400,
                            detail="An open product needs an end_time in the future")


@router.get('/', response_model=list[schemas.Show_Product])
def shwo_products(db: Session = Depends(get_db)):
    return db.query(models.Product).filter(models.Product.status == ProductStatus.open).all()


@router.get('/mine')
def my_products(db: Session = Depends(get_db),
                current_user: models.User = Depends(require_owner)):
    return db.query(models.Product).filter(
        models.Product.owner_id == current_user.id).all()


@router.post('/', response_model=schemas.Show_Product)
def create_product(data: schemas.Product, db: Session = Depends(get_db),
                   current_user: models.User = Depends(require_owner)):
    end_time = to_naive_utc(data.end_time)
    if data.status == "open":
        check_can_open(end_time)

    new_product = models.Product(
        name=data.name,
        title=data.title,
        owner_id=current_user.id,
        start_price=data.start_price,
        current_price=data.start_price,
        end_time=end_time,
        status=ProductStatus(data.status),
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


@router.put('/{id}', response_model=schemas.Show_Product_Owner)
def update_product(id: int, data: schemas.ProductUpdate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(require_owner)):
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if product.owner_id != current_user.id and current_user.role.name != "admin":
        raise HTTPException(
            status_code=403, detail="You can only edit your own products")
    if not product:
        raise HTTPException(
            status_code=404, detail=f"product with id {id} not found")
    if product.owner_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="You can only edit your own products")
    if product.status not in (ProductStatus.draft, ProductStatus.open):
        raise HTTPException(
            status_code=400, detail="This product can no longer be edited")
    if product.status == ProductStatus.sold:
        raise HTTPException(
            status_code=400, detail="Sold products cannot be modified")
    changes = data.model_dump(exclude_unset=True)

    if "name" in changes:
        product.name = changes["name"]
    if "title" in changes:
        product.title = changes["title"]
    if "start_price" in changes:
        if product.the_number_of_auction > 0:
            raise HTTPException(status_code=400,
                                detail="Cannot change start_price after bids exist")
        product.start_price = changes["start_price"]
        product.current_price = changes["start_price"]
    if "end_time" in changes:
        product.end_time = to_naive_utc(changes["end_time"])
    if "status" in changes:
        if changes["status"] == "draft" and product.the_number_of_auction > 0:
            raise HTTPException(status_code=400,
                                detail="Cannot move to draft after bids exist")
        product.status = ProductStatus(changes["status"])

    if product.status == ProductStatus.open:
        check_can_open(product.end_time)

    db.commit()
    db.refresh(product)
    return product


@router.delete('/{id}')
def destroy(id: int, db: Session = Depends(get_db),
            current_user: models.User = Depends(require_owner)):
    product = db.query(models.Product).filter(
        models.Product.id == id).first()
    if product.owner_id != current_user.id and current_user.role.name != "admin":
        raise HTTPException(
            status_code=403, detail="You can only edit your own products")
    if product.first().status == ProductStatus.sold:
        raise HTTPException(
            status_code=400, detail="Sold products cannot be deleted")
    if not product.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"product with id {id} not found")

    if product.first().owner_id != current_user.id:
        raise HTTPException(status_code=403,
                            detail="You can only delete your own products")
    product.delete(synchronize_session=False)
    db.commit()
    return 'Done'
