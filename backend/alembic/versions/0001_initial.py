"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-03-03 10:45:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'product_groups',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('prom_uid', sa.String(length=128), nullable=True, unique=True),
        sa.Column('name', sa.String(length=512), nullable=False),
    )
    op.create_index('ix_product_groups_id', 'product_groups', ['id'])
    op.create_index('ix_product_groups_prom_uid', 'product_groups', ['prom_uid'])

    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('prom_uid', sa.String(length=128), nullable=False, unique=True),
        sa.Column('name', sa.String(length=1024), nullable=False),
        sa.Column('price', sa.Numeric(12, 2), nullable=False),
        sa.Column('qty', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('availability', sa.String(length=64), nullable=False, server_default='available'),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('product_groups.id'), nullable=True),
    )
    op.create_index('ix_products_id', 'products', ['id'])
    op.create_index('ix_products_prom_uid', 'products', ['prom_uid'])
    op.create_index('ix_products_name', 'products', ['name'])

    movement_type_enum = sa.Enum('IN', 'OUT', 'ADJUST', name='movementtype')
    movement_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'inventory_movements',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('movement_type', movement_type_enum, nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_inventory_movements_id', 'inventory_movements', ['id'])
    op.create_index('ix_inventory_movements_product_id', 'inventory_movements', ['product_id'])
    op.create_index('ix_inventory_movements_created_at', 'inventory_movements', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_inventory_movements_created_at', table_name='inventory_movements')
    op.drop_index('ix_inventory_movements_product_id', table_name='inventory_movements')
    op.drop_index('ix_inventory_movements_id', table_name='inventory_movements')
    op.drop_table('inventory_movements')

    movement_type_enum = sa.Enum('IN', 'OUT', 'ADJUST', name='movementtype')
    movement_type_enum.drop(op.get_bind(), checkfirst=True)

    op.drop_index('ix_products_name', table_name='products')
    op.drop_index('ix_products_prom_uid', table_name='products')
    op.drop_index('ix_products_id', table_name='products')
    op.drop_table('products')

    op.drop_index('ix_product_groups_prom_uid', table_name='product_groups')
    op.drop_index('ix_product_groups_id', table_name='product_groups')
    op.drop_table('product_groups')
