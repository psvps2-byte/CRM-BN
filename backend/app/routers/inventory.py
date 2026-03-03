from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models import InventoryMovement, MovementType, Product
from app.schemas import InventoryMovementCreate, InventoryMovementOut

router = APIRouter(prefix='/inventory', tags=['inventory'])


@router.post('/movements', response_model=InventoryMovementOut, dependencies=[Depends(require_admin)])
def create_movement(payload: InventoryMovementCreate, db: Session = Depends(get_db)):
    product = db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found')

    if payload.movement_type in {MovementType.IN, MovementType.OUT} and payload.quantity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Quantity must be positive for IN/OUT')

    if payload.movement_type == MovementType.IN:
        product.qty += payload.quantity
    elif payload.movement_type == MovementType.OUT:
        if payload.quantity <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Quantity must be positive for OUT movement')
        if product.qty < payload.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Not enough quantity for OUT movement')
        product.qty -= payload.quantity
    elif payload.movement_type == MovementType.ADJUST:
        if payload.quantity < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Quantity cannot be negative for ADJUST')
        product.qty = payload.quantity

    movement = InventoryMovement(
        product_id=payload.product_id,
        movement_type=payload.movement_type,
        quantity=payload.quantity,
        note=payload.note,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)

    return InventoryMovementOut(
        id=movement.id,
        product_id=product.id,
        product_name=product.name,
        movement_type=movement.movement_type,
        quantity=movement.quantity,
        note=movement.note,
        created_at=movement.created_at,
    )


@router.get('/movements', response_model=list[InventoryMovementOut], dependencies=[Depends(require_admin)])
def list_movements(limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)):
    stmt = (
        select(InventoryMovement, Product.name)
        .join(Product, InventoryMovement.product_id == Product.id)
        .order_by(desc(InventoryMovement.created_at))
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [
        InventoryMovementOut(
            id=movement.id,
            product_id=movement.product_id,
            product_name=product_name,
            movement_type=movement.movement_type,
            quantity=movement.quantity,
            note=movement.note,
            created_at=movement.created_at,
        )
        for movement, product_name in rows
    ]
