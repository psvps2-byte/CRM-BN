from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, importer, inventory, orders, products, prom, r2

app = FastAPI(title=settings.app_name)

allowed_origins = [origin.strip() for origin in settings.cors_origin.split(',') if origin.strip()]
if not allowed_origins:
    allowed_origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(auth.router)
app.include_router(importer.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(prom.router)
app.include_router(r2.router)


@app.get('/health')
def healthcheck():
    return {'status': 'ok'}
