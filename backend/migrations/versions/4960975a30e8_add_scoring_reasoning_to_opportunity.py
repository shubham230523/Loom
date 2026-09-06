"""add_scoring_reasoning_to_opportunity

Revision ID: 4960975a30e8
Revises: ac4fba19cc7d
Create Date: 2026-09-06 11:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4960975a30e8'
down_revision: Union[str, None] = 'ac4fba19cc7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('opportunities', sa.Column('scoring_reasoning', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('opportunities', 'scoring_reasoning')
