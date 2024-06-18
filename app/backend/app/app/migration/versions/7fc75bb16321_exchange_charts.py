"""exchange_charts

Revision ID: 7fc75bb16321
Revises: c38a5d2d1f23
Create Date: 2024-06-17 16:28:39.549230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fc75bb16321'
down_revision: Union[str, None] = 'c38a5d2d1f23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('exchange_volume_chart_1d',
    sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('exchange_id', sa.BIGINT(), nullable=True),
    sa.Column('volume_usd', sa.NUMERIC(), nullable=True),
    sa.Column('timestamp', sa.BIGINT(), nullable=True),
    sa.ForeignKeyConstraint(['exchange_id'], ['exchange.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('exchange_id', 'timestamp', name='exchange_stamp_unique_1d')
    )
    op.create_table('exchange_volume_chart_1h',
    sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('exchange_id', sa.BIGINT(), nullable=True),
    sa.Column('volume_usd', sa.NUMERIC(), nullable=True),
    sa.Column('timestamp', sa.BIGINT(), nullable=True),
    sa.ForeignKeyConstraint(['exchange_id'], ['exchange.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('exchange_id', 'timestamp', name='exchange_stamp_unique_1h')
    )
    op.create_table('exchange_volume_chart_5m',
    sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('exchange_id', sa.BIGINT(), nullable=True),
    sa.Column('volume_usd', sa.NUMERIC(), nullable=True),
    sa.Column('timestamp', sa.BIGINT(), nullable=True),
    sa.ForeignKeyConstraint(['exchange_id'], ['exchange.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('exchange_id', 'timestamp', name='exchange_stamp_unique_5m')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('exchange_volume_chart_5m')
    op.drop_table('exchange_volume_chart_1h')
    op.drop_table('exchange_volume_chart_1d')
    # ### end Alembic commands ###