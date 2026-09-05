"""create_issues_table

Revision ID: e5a211b931d4
Revises: 6fac2f802609
Create Date: 2026-09-05 21:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5a211b931d4'
down_revision: Union[str, None] = '6fac2f802609'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('github_issue_id', sa.Integer(), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('labels', sa.JSON(), nullable=True),
        sa.Column('state', sa.String(length=50), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=False),
        sa.Column('html_url', sa.String(length=1024), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_issues_github_issue_id'), 'issues', ['github_issue_id'], unique=True)
    op.create_index(op.f('ix_issues_number'), 'issues', ['number'], unique=False)
    op.create_index(op.f('ix_issues_repository_id'), 'issues', ['repository_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_issues_repository_id'), table_name='issues')
    op.drop_index(op.f('ix_issues_number'), table_name='issues')
    op.drop_index(op.f('ix_issues_github_issue_id'), table_name='issues')
    op.drop_table('issues')
