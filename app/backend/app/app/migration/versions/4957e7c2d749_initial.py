"""initial

Revision ID: 4957e7c2d749
Revises: 
Create Date: 2024-04-17 16:51:53.840945

"""
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '4957e7c2d749'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dump_path = Path(__file__).parent.parent.absolute() / 'schema.dump'

    with open(dump_path, 'r') as sql_reader:
        op.execute(text(sql_reader.read()))

    op.execute(text('SET search_path = public'))


def downgrade() -> None:
    pass
