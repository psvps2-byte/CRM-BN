from threading import Lock

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.dependencies import require_admin
from app.schemas import SyncAllResult, SyncResult, SyncTriggerResult
from app.services.prom_sync import sync_orders_from_prom, sync_products_from_prom

router = APIRouter(prefix='/prom', tags=['prom'], dependencies=[Depends(require_admin)])
orders_sync_lock = Lock()


def _run_orders_sync_in_background() -> None:
    if not orders_sync_lock.acquire(blocking=False):
        return

    db = SessionLocal()
    try:
        sync_orders_from_prom(db)
    finally:
        db.close()
        orders_sync_lock.release()


@router.post('/sync/products', response_model=SyncResult)
def sync_products(db: Session = Depends(get_db)):
    synced = sync_products_from_prom(db)
    return SyncResult(synced=synced)


@router.post('/sync/orders', response_model=SyncTriggerResult)
def sync_orders(background_tasks: BackgroundTasks):
    if orders_sync_lock.locked():
        return SyncTriggerResult(started=False, message='Orders sync is already running')

    background_tasks.add_task(_run_orders_sync_in_background)
    return SyncTriggerResult(started=True, message='Orders sync started in background')


@router.post('/sync/all', response_model=SyncAllResult)
def sync_all(db: Session = Depends(get_db)):
    products_synced = sync_products_from_prom(db)
    orders_synced = sync_orders_from_prom(db)
    return SyncAllResult(products_synced=products_synced, orders_synced=orders_synced)
