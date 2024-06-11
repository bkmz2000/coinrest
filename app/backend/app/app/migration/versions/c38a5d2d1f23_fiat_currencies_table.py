"""fiat_currencies table

Revision ID: c38a5d2d1f23
Revises: 140bee9f7c84
Create Date: 2024-06-10 21:45:10.501172

"""
from typing import Sequence, Union

from src.db.models import UnixTimestamp
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c38a5d2d1f23'
down_revision: Union[str, None] = '140bee9f7c84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('fiat_currency_rates',
    sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('currency', sa.TEXT(), nullable=True),
    sa.Column('rate', sa.NUMERIC(), nullable=True),
    sa.Column('updated_at', UnixTimestamp(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('currency', name='fiat_currency_unique_symbol')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('fiat_currency_rates')
    # ### end Alembic commands ###
