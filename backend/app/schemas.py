from datetime import datetime

from pydantic import BaseModel, Field

from app.models import MovementType


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class ProductBase(BaseModel):
    name: str
    prom_uid: str
    price: float
    qty: int
    availability: str
    group_id: int | None = None


class ProductOut(ProductBase):
    id: int
    group_name: str | None = None

    class Config:
        from_attributes = True


class ProductUpdate(BaseModel):
    price: float = Field(ge=0)
    qty: int = Field(ge=0)
    availability: str = Field(min_length=1, max_length=64)


class ProductListResponse(BaseModel):
    items: list[ProductOut]
    page: int
    per_page: int
    total: int


class InventoryMovementCreate(BaseModel):
    product_id: int
    movement_type: MovementType
    quantity: int = Field(ge=0)
    note: str | None = None


class InventoryMovementOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    movement_type: MovementType
    quantity: int
    note: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class SignedUrlRequest(BaseModel):
    object_key: str = Field(min_length=1)
    mime: str = Field(min_length=1)


class SignedDownloadRequest(BaseModel):
    object_key: str = Field(min_length=1)


class SignedUrlResponse(BaseModel):
    url: str
    object_key: str


class SyncResult(BaseModel):
    synced: int


class SyncAllResult(BaseModel):
    products_synced: int
    orders_synced: int


class OrderItemOut(BaseModel):
    id: int
    product_id: int | None
    product_prom_uid: str | None
    name: str
    sku: str | None
    quantity: int
    price: float


class OrderOut(BaseModel):
    id: int
    prom_uid: str
    status: str
    total_price: float
    currency: str
    customer_name: str | None
    customer_phone: str | None
    customer_email: str | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut]


class OrderListResponse(BaseModel):
    items: list[OrderOut]
    page: int
    per_page: int
    total: int
