from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Product, PromOrder, PromOrderItem
from app.services.prom_api import fetch_all


def _to_decimal(value: Any, default: str = '0') -> Decimal:
    if value is None or value == '':
        return Decimal(default)
    try:
        return Decimal(str(value).replace(',', '.'))
    except Exception:
        return Decimal(default)


def _to_int(value: Any, default: int = 0) -> int:
    if value is None or value == '':
        return default
    try:
        return int(float(value))
    except Exception:
        return default


def _pick(data: dict[str, Any], keys: list[str], fallback: Any = None) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ''):
            return data[key]
    return fallback


def sync_products_from_prom(db: Session) -> int:
    remote_products = fetch_all(settings.prom_products_endpoint, ['products', 'product_list'])

    # Prom can return duplicate product IDs in one response. Keep only the latest row per UID.
    normalized_products: dict[str, dict[str, Any]] = {}
    for item in remote_products:
        prom_uid = _pick(item, ['id', 'prom_uid', 'uid', 'external_id'])
        if prom_uid is None:
            continue
        prom_uid = str(prom_uid).strip()
        if not prom_uid:
            continue

        normalized_products[prom_uid] = {
            'name': str(_pick(item, ['name', 'title'], prom_uid)).strip(),
            'price': _to_decimal(_pick(item, ['price', 'price_selling', 'price_with_discount'], 0)),
            'qty': max(0, _to_int(_pick(item, ['quantity_in_stock', 'quantity', 'stock'], 0))),
            'availability': str(_pick(item, ['presence', 'status', 'availability'], 'available')).strip() or 'available',
        }

    if not normalized_products:
        return 0

    existing_products = db.scalars(select(Product).where(Product.prom_uid.in_(list(normalized_products.keys())))).all()
    existing_by_uid = {product.prom_uid: product for product in existing_products}

    synced = 0
    for prom_uid, payload in normalized_products.items():
        product = existing_by_uid.get(prom_uid)
        if product:
            product.name = payload['name'] or product.name
            product.price = payload['price']
            product.qty = payload['qty']
            product.availability = payload['availability']
        else:
            db.add(
                Product(
                    prom_uid=prom_uid,
                    name=payload['name'] or prom_uid,
                    price=payload['price'],
                    qty=payload['qty'],
                    availability=payload['availability'],
                )
            )
        synced += 1

    db.commit()
    return synced


def sync_orders_from_prom(db: Session) -> int:
    remote_orders = fetch_all(settings.prom_orders_endpoint, ['orders', 'order_list'])

    synced = 0
    for item in remote_orders:
        prom_uid = _pick(item, ['id', 'order_id', 'number'])
        if prom_uid is None:
            continue
        prom_uid = str(prom_uid).strip()
        if not prom_uid:
            continue

        order = db.scalar(select(PromOrder).where(PromOrder.prom_uid == prom_uid))
        if not order:
            order = PromOrder(prom_uid=prom_uid)
            db.add(order)
            db.flush()

        customer = item.get('client') if isinstance(item.get('client'), dict) else {}
        first_name = str(customer.get('first_name') or '').strip()
        last_name = str(customer.get('last_name') or '').strip()
        full_name = ' '.join(part for part in [first_name, last_name] if part).strip() or None

        order.status = str(_pick(item, ['status', 'state'], 'new'))
        order.total_price = _to_decimal(_pick(item, ['price', 'total_price', 'amount'], 0))
        order.currency = str(_pick(item, ['currency', 'currency_code'], 'UAH'))
        order.customer_name = full_name or str(_pick(item, ['client_name', 'full_name'], '')) or None
        order.customer_phone = str(_pick(customer, ['phone', 'phone_number'], _pick(item, ['phone'], ''))) or None
        order.customer_email = str(_pick(customer, ['email'], _pick(item, ['email'], ''))) or None
        order.raw_payload = item

        order.items.clear()
        raw_items = item.get('products') or item.get('items') or []
        if isinstance(raw_items, list):
            for raw in raw_items:
                if not isinstance(raw, dict):
                    continue
                product_uid_raw = _pick(raw, ['id', 'product_id', 'external_id', 'sku'])
                product_uid = str(product_uid_raw).strip() if product_uid_raw is not None else None

                linked_product = None
                if product_uid:
                    linked_product = db.scalar(select(Product).where(Product.prom_uid == product_uid))

                order.items.append(
                    PromOrderItem(
                        product_id=linked_product.id if linked_product else None,
                        product_prom_uid=product_uid,
                        name=str(_pick(raw, ['name', 'title'], 'Item')),
                        sku=str(_pick(raw, ['sku'], '')) or None,
                        quantity=max(1, _to_int(_pick(raw, ['quantity', 'count'], 1), 1)),
                        price=_to_decimal(_pick(raw, ['price', 'price_selling'], 0)),
                    )
                )

        synced += 1

    db.commit()
    return synced
