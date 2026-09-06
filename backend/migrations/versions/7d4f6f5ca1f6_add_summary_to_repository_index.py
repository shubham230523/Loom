"""add_summary_to_repository_index

Revision ID: 7d4f6f5ca1f6
Revises: 626a15a616f6
Create Date: 2026-09-06 09:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7d4f6f5ca1f6'
down_revision: Union[str, None] = '626a15a616f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('repository_indexes', sa.Column('summary', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('repository_indexes', 'summary')
