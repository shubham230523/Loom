"""create_indexing_tables

Revision ID: 1dd30a024465
Revises: 5be00d572fc6
Create Date: 2026-09-06 02:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1dd30a024465'
down_revision: Union[str, None] = 'cd1eae625e46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create repository_indexes table
    op.create_table(
        'repository_indexes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('repository_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch', sa.String(length=100), nullable=False),
        sa.Column('commit_sha', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_info', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_repository_indexes_commit_sha'), 'repository_indexes', ['commit_sha'], unique=False)
    op.create_index(op.f('ix_repository_indexes_repository_id'), 'repository_indexes', ['repository_id'], unique=False)

    # 2. Create repository_files table
    op.create_table(
        'repository_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('repository_index_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('path', sa.String(length=1024), nullable=False),
        sa.Column('size_kb', sa.Float(), nullable=False),
        sa.Column('content_hash', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['repository_index_id'], ['repository_indexes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_repository_files_path'), 'repository_files', ['path'], unique=False)
    op.create_index(op.f('ix_repository_files_repository_index_id'), 'repository_files', ['repository_index_id'], unique=False)

    # 3. Create repository_symbols table
    op.create_table(
        'repository_symbols',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('repository_file_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=512), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=False),
        sa.Column('start_line', sa.Integer(), nullable=False),
        sa.Column('end_line', sa.Integer(), nullable=False),
        sa.Column('start_column', sa.Integer(), nullable=False),
        sa.Column('end_column', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['repository_file_id'], ['repository_files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_repository_symbols_name'), 'repository_symbols', ['name'], unique=False)
    op.create_index(op.f('ix_repository_symbols_repository_file_id'), 'repository_symbols', ['repository_file_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_repository_symbols_repository_file_id'), table_name='repository_symbols')
    op.drop_index(op.f('ix_repository_symbols_name'), table_name='repository_symbols')
    op.drop_table('repository_symbols')
    op.drop_index(op.f('ix_repository_files_repository_index_id'), table_name='repository_files')
    op.drop_index(op.f('ix_repository_files_path'), table_name='repository_files')
    op.drop_table('repository_files')
    op.drop_index(op.f('ix_repository_indexes_repository_id'), table_name='repository_indexes')
    op.drop_index(op.f('ix_repository_indexes_commit_sha'), table_name='repository_indexes')
    op.drop_table('repository_indexes')
