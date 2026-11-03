from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import schemas, models
from ..database import get_db
from ..deps import get_current_user, require_customer, require_owner
from ..models import ProductStatus, BidStatus
from .product import utcnow

router = APIRouter(tags=['bids'])

MIN_INCREMENT = Decimal("1.00")


def finalize_if_expired(product):
    if (product.status == ProductStatus.open
            and product.end_time is not None
            and product.end_time <= utcnow()):
        product.status = (ProductStatus.ended if product.id > 0
                          else ProductStatus.closed)


@router.post('/products/{id}/bids', response_model=schemas.Show_Bid, status_code=201)
def place_bid(id: int, data: schemas.BidCreate, db: Session = Depends(get_db),
              current_user: models.User = Depends(require_customer)):
    product = (db.query(models.Product)
               .filter(models.Product.id == id)
               .with_for_update()
               .first())
    if not product:
        raise HTTPException(
            status_code=404, detail=f"product with id {id} not found")

    if product.owner_id == current_user.id:
        raise HTTPException(
            status_code=403, detail="You cannot bid on your own product")
    if (product.status != ProductStatus.open
            or product.end_time is None
            or product.end_time <= utcnow()):
        raise HTTPException(status_code=400, detail="This auction is not open")

    if product.the_number_of_auction == 0:
        min_allowed = product.start_price
    else:
        min_allowed = product.current_price + MIN_INCREMENT

    if data.amount < min_allowed:
        raise HTTPException(
            status_code=400, detail=f"Bid must be at least {min_allowed}")

    bid = models.Bid(product_id=product.id,
                     bidder_id=current_user.id, amount=data.amount)
    product.current_price = data.amount
    product.the_number_of_auction += 1

    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid


@router.get('/products/{id}/bids', response_model=list[schemas.Show_Bid])
def product_bids(id: int, db: Session = Depends(get_db),
                 current_user: models.User = Depends(require_owner)):
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if not product:
        raise HTTPException(
            status_code=404, detail=f"product with id {id} not found")
    if product.owner_id != current_user.id and current_user.role.name != "admin":
        raise HTTPException(
            status_code=403, detail="Only the product owner can see its bids")

    return (db.query(models.Bid)
            .filter(models.Bid.product_id == id)
            .order_by(models.Bid.amount.desc())
            .all())


@router.post('/bids/{bid_id}/accept', response_model=schemas.Show_Bid)
def accept_bid(bid_id: int, db: Session = Depends(get_db),
               current_user: models.User = Depends(require_owner)):
    bid = db.query(models.Bid).filter(models.Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(
            status_code=404, detail=f"bid with id {bid_id} not found")

    product = (db.query(models.Product)
               .filter(models.Product.id == bid.product_id)
               .with_for_update()
               .first())

    if product.owner_id != current_user.id and current_user.role.name != "admin":
        raise HTTPException(
            status_code=403, detail="Only the product owner can accept bids")

    finalize_if_expired(product)

    if product.status == ProductStatus.sold:
        raise HTTPException(
            status_code=400, detail="This product is already sold")
    if product.status != ProductStatus.ended:
        raise HTTPException(
            status_code=400, detail="The auction has not ended yet")
    if bid.status != BidStatus.pending:
        raise HTTPException(status_code=400, detail="This bid is not pending")

    best = (db.query(func.max(models.Bid.amount))
            .filter(models.Bid.product_id == product.id)
            .scalar())
    if bid.amount != best:
        raise HTTPException(
            status_code=400, detail="Only the highest bid can be accepted")

    (db.query(models.Bid)
       .filter(models.Bid.product_id == product.id, models.Bid.id != bid.id)
       .update({"status": BidStatus.rejected}, synchronize_session=False))
    bid.status = BidStatus.accepted
    product.status = ProductStatus.sold
    product.accepted_bid_id = bid.id

    db.commit()
    db.refresh(bid)
    return bid


@router.get('/bids/me', response_model=list[schemas.Show_Bid])
def my_bids(db: Session = Depends(get_db),
            current_user: models.User = Depends(get_current_user)):
    return (db.query(models.Bid)
            .filter(models.Bid.bidder_id == current_user.id)
            .order_by(models.Bid.id.desc())
            .all())
