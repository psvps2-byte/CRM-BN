from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import Product, ProductGroup
from app.schemas import ProductListResponse, ProductOut, ProductUpdate

router = APIRouter(prefix='/products', tags=['products'])


@router.get('', response_model=ProductListResponse, dependencies=[Depends(require_admin)])
def list_products(
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    conditions = []
    if q:
        pattern = f'%{q.strip()}%'
        conditions.append(or_(Product.name.ilike(pattern), Product.prom_uid.ilike(pattern)))

    total_stmt = select(func.count(Product.id))
    if conditions:
        total_stmt = total_stmt.where(*conditions)
    total = db.scalar(total_stmt) or 0

    stmt = select(Product, ProductGroup.name).join(ProductGroup, Product.group_id == ProductGroup.id, isouter=True)
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.order_by(Product.id.desc()).offset((page - 1) * per_page).limit(per_page)

    rows = db.execute(stmt).all()
    items = [
        ProductOut(
            id=product.id,
            prom_uid=product.prom_uid,
            name=product.name,
            price=float(product.price),
            qty=product.qty,
            availability=product.availability,
            group_id=product.group_id,
            group_name=group_name,
        )
        for product, group_name in rows
    ]
    return ProductListResponse(items=items, page=page, per_page=per_page, total=total)


@router.patch('/{product_id}', response_model=ProductOut, dependencies=[Depends(require_admin)])
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found')

    product.price = payload.price
    product.qty = payload.qty
    product.availability = payload.availability
    db.commit()
    db.refresh(product)

    group_name = None
    if product.group_id:
        group = db.get(ProductGroup, product.group_id)
        group_name = group.name if group else None

    return ProductOut(
        id=product.id,
        prom_uid=product.prom_uid,
        name=product.name,
        price=float(product.price),
        qty=product.qty,
        availability=product.availability,
        group_id=product.group_id,
        group_name=group_name,
    )
