from fastapi import APIRouter, Depends, status, HTTPException, Query, File, UploadFile
from sqlalchemy.orm import Session
from .. import schemas, models
from ..database import get_db
from ..deps import require_owner, get_current_user
from datetime import datetime, timezone
from ..models import ProductStatus
import csv
import io
from decimal import Decimal, InvalidOperation


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


def read_csv_products(file: UploadFile):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    try:
        text = file.file.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))
    headers = {h.strip() for h in (reader.fieldnames or [])}
    if not {"name", "title", "start_price"}.issubset(headers):
        raise HTTPException(status_code=400,
                            detail="CSV must have columns: name, title, start_price")

    preview = []
    for line_no, raw_row in enumerate(reader, start=2):
        row = {k.strip(): (v or "").strip() for k, v in raw_row.items() if k}
        item = {"row": line_no, "name": row.get("name", ""),
                "title": row.get("title", ""),
                "start_price": row.get("start_price", ""),
                "status": row.get("status") or "draft",
                "end_time": row.get("end_time") or None}
        try:
            if not row.get("name") or not row.get("title"):
                raise ValueError("name and title are required")

            try:
                price = Decimal(row["start_price"])
            except InvalidOperation:
                raise ValueError("start_price is not a number")
            if not price.is_finite() or price < 0 or price >= Decimal("10000000000"):
                raise ValueError("start_price is out of range")
            price = price.quantize(Decimal("0.01"))

            row_status = row.get("status") or "draft"
            if row_status not in ("draft", "open"):
                raise ValueError("status must be draft or open")

            end_time = None
            if row.get("end_time"):
                try:
                    end_time = to_naive_utc(
                        datetime.fromisoformat(row["end_time"].replace("Z", "+00:00")))
                except ValueError:
                    raise ValueError("end_time format is invalid")

            if row_status == "open" and (end_time is None or end_time <= utcnow()):
                raise ValueError("an open product needs an end_time in the future")

            item.update({"start_price": str(price), "status": row_status,
                         "end_time": end_time.isoformat() if end_time else None,
                         "valid": True, "error": None})
        except ValueError as e:
            item.update({"valid": False, "error": str(e)})

        preview.append(item)

    return preview


@router.post('/import/preview')
def preview_import(file: UploadFile = File(...),
                  current_user: models.User = Depends(require_owner)):
    rows = read_csv_products(file)
    return {"rows": rows, "valid": sum(row["valid"] for row in rows),
            "invalid": sum(not row["valid"] for row in rows)}


@router.post('/import/confirm')
def confirm_import(rows: list[dict], db: Session = Depends(get_db),
                  current_user: models.User = Depends(require_owner)):
    saved = 0
    errors = []

    for index, row in enumerate(rows, start=1):
        try:
            if not row.get("name") or not row.get("title"):
                raise ValueError("name and title are required")

            try:
                price = Decimal(str(row["start_price"]))
            except (InvalidOperation, KeyError):
                raise ValueError("start_price is not a number")
            if not price.is_finite() or price < 0 or price >= Decimal("10000000000"):
                raise ValueError("start_price is out of range")
            price = price.quantize(Decimal("0.01"))

            row_status = row.get("status") or "draft"
            if row_status not in ("draft", "open"):
                raise ValueError("status must be draft or open")

            end_time = None
            if row.get("end_time"):
                try:
                    end_time = to_naive_utc(datetime.fromisoformat(str(row["end_time"])))
                except ValueError:
                    raise ValueError("end_time format is invalid")
            if row_status == "open" and (end_time is None or end_time <= utcnow()):
                raise ValueError("an open product needs an end_time in the future")

            db.add(models.Product(name=row["name"].strip(), title=row["title"].strip(),
                                  owner_id=current_user.id, start_price=price,
                                  current_price=price, end_time=end_time,
                                  status=ProductStatus(row_status)))
            saved += 1
        except (ValueError, KeyError) as e:
            errors.append({"row": row.get("row", index), "error": str(e)})

    db.commit()
    return {"saved": saved, "failed": len(errors), "errors": errors}


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
    if product.status == ProductStatus.sold:
        raise HTTPException(
            status_code=400, detail="Sold products cannot be deleted")
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"product with id {id} not found")

    if product.owner_id != current_user.id:
        raise HTTPException(status_code=403,
                            detail="You can only delete your own products")
    db.delete(product)
    db.commit()
    return 'Done'
