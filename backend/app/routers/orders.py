from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import PromOrder
from app.schemas import OrderItemOut, OrderListResponse, OrderOut

router = APIRouter(prefix='/orders', tags=['orders'])


@router.get('', response_model=OrderListResponse, dependencies=[Depends(require_admin)])
def list_orders(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count(PromOrder.id))) or 0

    stmt = (
        select(PromOrder)
        .order_by(desc(PromOrder.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    orders = db.scalars(stmt).all()

    return OrderListResponse(
        items=[
            OrderOut(
                id=order.id,
                prom_uid=order.prom_uid,
                status=order.status,
                total_price=float(order.total_price),
                currency=order.currency,
                customer_name=order.customer_name,
                customer_phone=order.customer_phone,
                customer_email=order.customer_email,
                created_at=order.created_at,
                updated_at=order.updated_at,
                items=[
                    OrderItemOut(
                        id=item.id,
                        product_id=item.product_id,
                        product_prom_uid=item.product_prom_uid,
                        name=item.name,
                        sku=item.sku,
                        quantity=item.quantity,
                        price=float(item.price),
                    )
                    for item in order.items
                ],
            )
            for order in orders
        ],
        page=page,
        per_page=per_page,
        total=total,
    )
