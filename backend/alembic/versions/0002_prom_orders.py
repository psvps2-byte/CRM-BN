"""add prom orders tables

Revision ID: 0002_prom_orders
Revises: 0001_initial
Create Date: 2026-03-03 11:20:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_prom_orders'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'prom_orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('prom_uid', sa.String(length=128), nullable=False, unique=True),
        sa.Column('status', sa.String(length=128), nullable=False, server_default='new'),
        sa.Column('total_price', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=16), nullable=False, server_default='UAH'),
        sa.Column('customer_name', sa.String(length=255), nullable=True),
        sa.Column('customer_phone', sa.String(length=64), nullable=True),
        sa.Column('customer_email', sa.String(length=255), nullable=True),
        sa.Column('raw_payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_prom_orders_id', 'prom_orders', ['id'])
    op.create_index('ix_prom_orders_prom_uid', 'prom_orders', ['prom_uid'])
    op.create_index('ix_prom_orders_created_at', 'prom_orders', ['created_at'])
    op.create_index('ix_prom_orders_updated_at', 'prom_orders', ['updated_at'])

    op.create_table(
        'prom_order_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('prom_orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=True),
        sa.Column('product_prom_uid', sa.String(length=128), nullable=True),
        sa.Column('name', sa.String(length=1024), nullable=False),
        sa.Column('sku', sa.String(length=128), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('price', sa.Numeric(12, 2), nullable=False, server_default='0'),
    )
    op.create_index('ix_prom_order_items_id', 'prom_order_items', ['id'])
    op.create_index('ix_prom_order_items_order_id', 'prom_order_items', ['order_id'])
    op.create_index('ix_prom_order_items_product_id', 'prom_order_items', ['product_id'])
    op.create_index('ix_prom_order_items_product_prom_uid', 'prom_order_items', ['product_prom_uid'])


def downgrade() -> None:
    op.drop_index('ix_prom_order_items_product_prom_uid', table_name='prom_order_items')
    op.drop_index('ix_prom_order_items_product_id', table_name='prom_order_items')
    op.drop_index('ix_prom_order_items_order_id', table_name='prom_order_items')
    op.drop_index('ix_prom_order_items_id', table_name='prom_order_items')
    op.drop_table('prom_order_items')

    op.drop_index('ix_prom_orders_updated_at', table_name='prom_orders')
    op.drop_index('ix_prom_orders_created_at', table_name='prom_orders')
    op.drop_index('ix_prom_orders_prom_uid', table_name='prom_orders')
    op.drop_index('ix_prom_orders_id', table_name='prom_orders')
    op.drop_table('prom_orders')
