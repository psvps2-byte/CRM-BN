from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.services.importer import import_prom_xlsx

router = APIRouter(prefix='/import', tags=['import'])


@router.post('/prom-xlsx', dependencies=[Depends(require_admin)])
def import_prom(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = file.file.read()
    result = import_prom_xlsx(db, content)
    return {'status': 'ok', **result}
