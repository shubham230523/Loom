"""create_repositories_table

Revision ID: 6fac2f802609
Revises: 78699cf097ba
Create Date: 2026-09-05 21:50:57.737362

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6fac2f802609'
down_revision: Union[str, None] = '78699cf097ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'repositories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('github_repo_id', sa.Integer(), nullable=False),
        sa.Column('owner', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=512), nullable=False),
        sa.Column('html_url', sa.String(length=1024), nullable=False),
        sa.Column('description', sa.String(length=2048), nullable=True),
        sa.Column('default_branch', sa.String(length=100), nullable=False),
        sa.Column('language', sa.String(length=100), nullable=True),
        sa.Column('stargazers_count', sa.Integer(), nullable=False),
        sa.Column('forks_count', sa.Integer(), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_repositories_full_name'), 'repositories', ['full_name'], unique=True)
    op.create_index(op.f('ix_repositories_github_repo_id'), 'repositories', ['github_repo_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_repositories_github_repo_id'), table_name='repositories')
    op.drop_index(op.f('ix_repositories_full_name'), table_name='repositories')
    op.drop_table('repositories')
