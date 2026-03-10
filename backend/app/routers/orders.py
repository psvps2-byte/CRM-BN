from copy import deepcopy

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import PromOrder
from app.schemas import OrderItemOut, OrderListResponse, OrderOut, OrderUpdate

router = APIRouter(prefix='/orders', tags=['orders'])


def _pick_nested(payload: dict | None, paths: list[tuple[str, ...]]) -> str | None:
    if not isinstance(payload, dict):
        return None
    for path in paths:
        current = payload
        found = True
        for part in path:
            if not isinstance(current, dict) or part not in current:
                found = False
                break
            current = current[part]
        if found and current not in (None, ''):
            return str(current)
    return None


def _set_nested(payload: dict, path: tuple[str, ...], value: str | None) -> None:
    current = payload
    for part in path[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            current[part] = next_value
        current = next_value
    current[path[-1]] = value


def _serialize_order(order: PromOrder) -> OrderOut:
    payload = order.raw_payload if isinstance(order.raw_payload, dict) else {}
    payment_method = _pick_nested(payload, [('payment_option',), ('payment',), ('payment_method',)])
    shipping_method = _pick_nested(
        payload,
        [('delivery_option',), ('delivery',), ('delivery_service',), ('delivery_method',)],
    )
    shipping_address = _pick_nested(
        payload,
        [('delivery_address',), ('address',), ('delivery', 'address'), ('shipping_address',)],
    )
    shipping_city = _pick_nested(
        payload,
        [('delivery', 'city'), ('shipping', 'city'), ('recipient_city',), ('city',)],
    )
    shipping_branch = _pick_nested(
        payload,
        [('delivery', 'warehouse'), ('shipping', 'branch'), ('branch',), ('recipient_branch',), ('ttn_warehouse',)],
    )
    comment = _pick_nested(
        payload,
        [('client_note',), ('note',), ('comment',), ('comments',), ('buyer_comment',)],
    )

    return OrderOut(
        id=order.id,
        prom_uid=order.prom_uid,
        status=order.status,
        total_price=float(order.total_price),
        currency=order.currency,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        customer_email=order.customer_email,
        payment_method=payment_method,
        shipping_method=shipping_method,
        shipping_address=shipping_address,
        shipping_city=shipping_city,
        shipping_branch=shipping_branch,
        comment=comment,
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
                line_total=float(item.price) * item.quantity,
            )
            for item in order.items
        ],
    )


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
        items=[_serialize_order(order) for order in orders],
        page=page,
        per_page=per_page,
        total=total,
    )


@router.patch('/{order_id}', response_model=OrderOut, dependencies=[Depends(require_admin)])
def update_order(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db)):
    order = db.get(PromOrder, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Order not found')

    changes = payload.model_dump(exclude_unset=True)
    raw_payload = deepcopy(order.raw_payload) if isinstance(order.raw_payload, dict) else {}

    if 'status' in changes and payload.status is not None:
        order.status = payload.status
        raw_payload['status'] = payload.status

    if 'customer_name' in changes:
        order.customer_name = payload.customer_name or None
        _set_nested(raw_payload, ('client', 'full_name'), payload.customer_name or None)

    if 'customer_phone' in changes:
        order.customer_phone = payload.customer_phone or None
        _set_nested(raw_payload, ('client', 'phone'), payload.customer_phone or None)

    if 'customer_email' in changes:
        order.customer_email = payload.customer_email or None
        _set_nested(raw_payload, ('client', 'email'), payload.customer_email or None)

    if 'payment_method' in changes:
        raw_payload['payment_option'] = payload.payment_method or None

    if 'shipping_method' in changes:
        raw_payload['delivery_option'] = payload.shipping_method or None

    if 'shipping_address' in changes:
        raw_payload['delivery_address'] = payload.shipping_address or None
        _set_nested(raw_payload, ('delivery', 'address'), payload.shipping_address or None)

    if 'shipping_city' in changes:
        _set_nested(raw_payload, ('delivery', 'city'), payload.shipping_city or None)
        raw_payload['recipient_city'] = payload.shipping_city or None

    if 'shipping_branch' in changes:
        _set_nested(raw_payload, ('delivery', 'warehouse'), payload.shipping_branch or None)
        raw_payload['recipient_branch'] = payload.shipping_branch or None

    if 'comment' in changes:
        raw_payload['client_note'] = payload.comment or None

    order.raw_payload = raw_payload
    db.commit()
    db.refresh(order)
    return _serialize_order(order)
