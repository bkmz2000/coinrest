"""exchnage field mapper

Revision ID: a7ef5ada8a70
Revises: 81bb3ed562ce
Create Date: 2024-04-23 12:03:00.922554

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7ef5ada8a70'
down_revision: Union[str, None] = '81bb3ed562ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('exchange_tickers_mapper', 'exchange_id',
               existing_type=sa.SMALLINT(),
               type_=sa.BIGINT(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('exchange_tickers_mapper', 'exchange_id',
               existing_type=sa.BIGINT(),
               type_=sa.SMALLINT(),
               existing_nullable=True)
    # ### end Alembic commands ###
