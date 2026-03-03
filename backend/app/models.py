import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MovementType(str, enum.Enum):
    IN = 'IN'
    OUT = 'OUT'
    ADJUST = 'ADJUST'


class ProductGroup(Base):
    __tablename__ = 'product_groups'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prom_uid: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)

    products: Mapped[list['Product']] = relationship('Product', back_populates='group')


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prom_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    qty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    availability: Mapped[str] = mapped_column(String(64), nullable=False, default='available')
    group_id: Mapped[int | None] = mapped_column(ForeignKey('product_groups.id'), nullable=True)

    group: Mapped[ProductGroup | None] = relationship('ProductGroup', back_populates='products')
    movements: Mapped[list['InventoryMovement']] = relationship('InventoryMovement', back_populates='product')
    order_items: Mapped[list['PromOrderItem']] = relationship('PromOrderItem', back_populates='product')


class InventoryMovement(Base):
    __tablename__ = 'inventory_movements'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'), nullable=False, index=True)
    movement_type: Mapped[MovementType] = mapped_column(Enum(MovementType), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    product: Mapped[Product] = relationship('Product', back_populates='movements')


class PromOrder(Base):
    __tablename__ = 'prom_orders'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prom_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(128), nullable=False, default='new')
    total_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(16), nullable=False, default='UAH')
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True
    )

    items: Mapped[list['PromOrderItem']] = relationship(
        'PromOrderItem', back_populates='order', cascade='all, delete-orphan'
    )


class PromOrderItem(Base):
    __tablename__ = 'prom_order_items'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('prom_orders.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey('products.id'), nullable=True, index=True)
    product_prom_uid: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(1024), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(128), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    order: Mapped[PromOrder] = relationship('PromOrder', back_populates='items')
    product: Mapped[Product | None] = relationship('Product', back_populates='order_items')
