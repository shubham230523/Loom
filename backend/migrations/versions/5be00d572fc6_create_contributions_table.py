"""create_contributions_table

Revision ID: 5be00d572fc6
Revises: 61d41cceb6b7
Create Date: 2026-09-05 22:06:38.560710

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5be00d572fc6'
down_revision: Union[str, None] = '61d41cceb6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'contributions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('opportunity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('branch_name', sa.String(length=255), nullable=True),
        sa.Column('workspace_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['opportunity_id'], ['opportunities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contributions_opportunity_id'), 'contributions', ['opportunity_id'], unique=False)
    op.create_index(op.f('ix_contributions_repository_id'), 'contributions', ['repository_id'], unique=False)
    op.create_index(op.f('ix_contributions_user_id'), 'contributions', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_contributions_user_id'), table_name='contributions')
    op.drop_index(op.f('ix_contributions_repository_id'), table_name='contributions')
    op.drop_index(op.f('ix_contributions_opportunity_id'), table_name='contributions')
    op.drop_table('contributions')
