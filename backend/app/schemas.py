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
    slug: str | None = None
    description: str | None = None
    attributes: dict[str, str] | None = None
    image_urls: list[str] | None = None


class ProductOut(ProductBase):
    id: int
    group_name: str | None = None

    class Config:
        from_attributes = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=1024)
    price: float | None = Field(default=None, ge=0)
    qty: int | None = Field(default=None, ge=0)
    availability: str | None = Field(default=None, min_length=1, max_length=64)
    slug: str | None = Field(default=None, max_length=1024)
    description: str | None = None
    attributes: dict[str, str] | None = None
    image_urls: list[str] | None = None


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
    line_total: float


class OrderOut(BaseModel):
    id: int
    prom_uid: str
    status: str
    total_price: float
    currency: str
    customer_name: str | None
    customer_phone: str | None
    customer_email: str | None
    payment_method: str | None
    shipping_method: str | None
    shipping_address: str | None
    shipping_city: str | None
    shipping_branch: str | None
    comment: str | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut]


class OrderListResponse(BaseModel):
    items: list[OrderOut]
    page: int
    per_page: int
    total: int


class OrderUpdate(BaseModel):
    status: str | None = Field(default=None, min_length=1, max_length=128)
    customer_name: str | None = None
    customer_phone: str | None = None
    customer_email: str | None = None
    payment_method: str | None = None
    shipping_method: str | None = None
    shipping_address: str | None = None
    shipping_city: str | None = None
    shipping_branch: str | None = None
    comment: str | None = None
