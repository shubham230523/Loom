"""create_code_reviews_table

Revision ID: cd1eae625e46
Revises: 349a543f2828
Create Date: 2026-09-05 22:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'cd1eae625e46'
down_revision: Union[str, None] = '349a543f2828'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'code_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('contribution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('review_issues', sa.JSON(), nullable=True),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['contribution_id'], ['contributions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_code_reviews_contribution_id'), 'code_reviews', ['contribution_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_code_reviews_contribution_id'), table_name='code_reviews')
    op.drop_table('code_reviews')
