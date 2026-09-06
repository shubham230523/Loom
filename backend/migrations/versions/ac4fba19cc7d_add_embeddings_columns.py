"""add_embeddings_columns

Revision ID: ac4fba19cc7d
Revises: 7d4f6f5ca1f6
Create Date: 2026-09-06 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = 'ac4fba19cc7d'
down_revision: Union[str, None] = '7d4f6f5ca1f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # 2. Add columns
    op.add_column('repository_indexes', sa.Column('embedding', Vector(768), nullable=True))
    op.add_column('repository_files', sa.Column('embedding', Vector(768), nullable=True))
    op.add_column('repository_symbols', sa.Column('embedding', Vector(768), nullable=True))
    op.add_column('issues', sa.Column('embedding', Vector(768), nullable=True))


def downgrade() -> None:
    op.drop_column('issues', 'embedding')
    op.drop_column('repository_symbols', 'embedding')
    op.drop_column('repository_files', 'embedding')
    op.drop_column('repository_indexes', 'embedding')
    # We don't drop the extension as other tables might use it
