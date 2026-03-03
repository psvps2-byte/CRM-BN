from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.schemas import SyncAllResult, SyncResult
from app.services.prom_sync import sync_orders_from_prom, sync_products_from_prom

router = APIRouter(prefix='/prom', tags=['prom'], dependencies=[Depends(require_admin)])


@router.post('/sync/products', response_model=SyncResult)
def sync_products(db: Session = Depends(get_db)):
    synced = sync_products_from_prom(db)
    return SyncResult(synced=synced)


@router.post('/sync/orders', response_model=SyncResult)
def sync_orders(db: Session = Depends(get_db)):
    synced = sync_orders_from_prom(db)
    return SyncResult(synced=synced)


@router.post('/sync/all', response_model=SyncAllResult)
def sync_all(db: Session = Depends(get_db)):
    products_synced = sync_products_from_prom(db)
    orders_synced = sync_orders_from_prom(db)
    return SyncAllResult(products_synced=products_synced, orders_synced=orders_synced)
