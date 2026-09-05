"""create_agent_runs_table

Revision ID: 74c1e39fb007
Revises: 5be00d572fc6
Create Date: 2026-09-05 22:08:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '74c1e39fb007'
down_revision: Union[str, None] = '5be00d572fc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'agent_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contribution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('current_step', sa.String(length=255), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_info', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['contribution_id'], ['contributions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_runs_contribution_id'), 'agent_runs', ['contribution_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_agent_runs_contribution_id'), table_name='agent_runs')
    op.drop_table('agent_runs')
