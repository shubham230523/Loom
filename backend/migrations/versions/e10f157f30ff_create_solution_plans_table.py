"""create_solution_plans_table

Revision ID: e10f157f30ff
Revises: 4960975a30e8
Create Date: 2026-09-06 11:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e10f157f30ff'
down_revision: Union[str, None] = '4960975a30e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'solution_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contribution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('problem', sa.Text(), nullable=False),
        sa.Column('root_cause', sa.Text(), nullable=False),
        sa.Column('relevant_files', sa.JSON(), nullable=False),
        sa.Column('relevant_symbols', sa.JSON(), nullable=False),
        sa.Column('implementation_steps', sa.JSON(), nullable=False),
        sa.Column('testing_strategy', sa.Text(), nullable=False),
        sa.Column('risks', sa.Text(), nullable=False),
        sa.Column('expected_diff_size', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['contribution_id'], ['contributions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contribution_id')
    )
    op.create_index(op.f('ix_solution_plans_contribution_id'), 'solution_plans', ['contribution_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_solution_plans_contribution_id'), table_name='solution_plans')
    op.drop_table('solution_plans')
