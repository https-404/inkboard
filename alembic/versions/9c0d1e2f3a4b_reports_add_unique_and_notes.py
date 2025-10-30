"""reports add unique and notes

Revision ID: 9c0d1e2f3a4b
Revises: 8a9b0c1d2e3f
Create Date: 2025-10-30
"""

from alembic import op
import sqlalchemy as sa


revision = '9c0d1e2f3a4b'
down_revision = '8a9b0c1d2e3f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('report', sa.Column('moderator_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('report', sa.Column('moderation_note', sa.Text(), nullable=True))
    op.create_unique_constraint('uq_report_article_reporter', 'report', ['article_id', 'reporter_id'])


def downgrade() -> None:
    op.drop_constraint('uq_report_article_reporter', 'report', type_='unique')
    op.drop_column('report', 'moderation_note')
    op.drop_column('report', 'moderator_id')


