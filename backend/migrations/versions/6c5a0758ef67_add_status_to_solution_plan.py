"""add_status_to_solution_plan

Revision ID: 6c5a0758ef67
Revises: e10f157f30ff
Create Date: 2026-09-06 11:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c5a0758ef67'
down_revision: Union[str, None] = 'e10f157f30ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('solution_plans', sa.Column('status', sa.String(length=50), server_default='pending', nullable=False))


def downgrade() -> None:
    op.drop_column('solution_plans', 'status')
