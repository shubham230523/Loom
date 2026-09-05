"""create_test_runs_table

Revision ID: 349a543f2828
Revises: 6bb46994ed5d
Create Date: 2026-09-05 22:16:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '349a543f2828'
down_revision: Union[str, None] = '6bb46994ed5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'test_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contribution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('command', sa.String(length=1024), nullable=False),
        sa.Column('exit_code', sa.Integer(), nullable=True),
        sa.Column('stdout', sa.Text(), nullable=True),
        sa.Column('stderr', sa.Text(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['contribution_id'], ['contributions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_test_runs_contribution_id'), 'test_runs', ['contribution_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_test_runs_contribution_id'), table_name='test_runs')
    op.drop_table('test_runs')
