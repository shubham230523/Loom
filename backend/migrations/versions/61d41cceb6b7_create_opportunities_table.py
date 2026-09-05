"""create_opportunities_table

Revision ID: 61d41cceb6b7
Revises: e5a211b931d4
Create Date: 2026-09-05 22:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '61d41cceb6b7'
down_revision: Union[str, None] = 'e5a211b931d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'opportunities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('impact', sa.String(length=50), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=False),
        sa.Column('reproducibility', sa.String(length=100), nullable=True),
        sa.Column('duplicate_risk', sa.String(length=100), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_opportunities_issue_id'), 'opportunities', ['issue_id'], unique=False)
    op.create_index(op.f('ix_opportunities_repository_id'), 'opportunities', ['repository_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_opportunities_repository_id'), table_name='opportunities')
    op.drop_index(op.f('ix_opportunities_issue_id'), table_name='opportunities')
    op.drop_table('opportunities')
