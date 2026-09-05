"""create_agent_events_table

Revision ID: 6bb46994ed5d
Revises: 74c1e39fb007
Create Date: 2026-09-05 22:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6bb46994ed5d'
down_revision: Union[str, None] = '74c1e39fb007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'agent_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['agent_run_id'], ['agent_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_events_agent_run_id'), 'agent_events', ['agent_run_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_agent_events_agent_run_id'), table_name='agent_events')
    op.drop_table('agent_events')
