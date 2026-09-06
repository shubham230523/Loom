"""create_model_runs_table

Revision ID: 626a15a616f6
Revises: 1dd30a024465
Create Date: 2026-09-06 09:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '626a15a616f6'
down_revision: Union[str, None] = '1dd30a024465'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'model_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('model', sa.String(length=255), nullable=False),
        sa.Column('task', sa.String(length=100), nullable=True),
        sa.Column('duration', sa.Float(), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False),
        sa.Column('completion_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_info', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_runs_model'), 'model_runs', ['model'], unique=False)
    op.create_index(op.f('ix_model_runs_provider'), 'model_runs', ['provider'], unique=False)
    op.create_index(op.f('ix_model_runs_task'), 'model_runs', ['task'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_model_runs_task'), table_name='model_runs')
    op.drop_index(op.f('ix_model_runs_provider'), table_name='model_runs')
    op.drop_index(op.f('ix_model_runs_model'), table_name='model_runs')
    op.drop_table('model_runs')
