"""add product meta fields

Revision ID: 0003_product_meta_fields
Revises: 0002_prom_orders
Create Date: 2026-03-08 21:10:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0003_product_meta_fields'
down_revision = '0002_prom_orders'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('products', sa.Column('slug', sa.String(length=1024), nullable=True))
    op.add_column('products', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('products', sa.Column('attributes', sa.JSON(), nullable=True))
    op.add_column('products', sa.Column('image_urls', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('products', 'image_urls')
    op.drop_column('products', 'attributes')
    op.drop_column('products', 'description')
    op.drop_column('products', 'slug')
