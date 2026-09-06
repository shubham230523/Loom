"""add_diff_summary_to_contribution

Revision ID: 5b8e5b4d7fe2
Revises: 6c5a0758ef67
Create Date: 2026-09-06 12:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b8e5b4d7fe2'
down_revision: Union[str, None] = '6c5a0758ef67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('contributions', sa.Column('diff_summary', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('contributions', 'diff_summary')
