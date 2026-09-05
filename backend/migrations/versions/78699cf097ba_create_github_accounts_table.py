"""create_github_accounts_table

Revision ID: 78699cf097ba
Revises: 461660ed1038
Create Date: 2026-09-05 21:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '78699cf097ba'
down_revision: Union[str, None] = '461660ed1038'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'github_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('github_id', sa.Integer(), nullable=False),
        sa.Column('access_token_encrypted', sa.String(length=2048), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_github_accounts_github_id'), 'github_accounts', ['github_id'], unique=True)
    op.create_index(op.f('ix_github_accounts_user_id'), 'github_accounts', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_github_accounts_user_id'), table_name='github_accounts')
    op.drop_index(op.f('ix_github_accounts_github_id'), table_name='github_accounts')
    op.drop_table('github_accounts')
