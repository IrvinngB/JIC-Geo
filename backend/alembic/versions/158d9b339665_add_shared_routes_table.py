"""add shared_routes table

Revision ID: 158d9b339665
Revises: a0133e5a7bdb
Create Date: 2026-09-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '158d9b339665'
down_revision: Union[str, None] = 'a0133e5a7bdb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'shared_routes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('history_id', sa.UUID(), nullable=False),
        sa.Column('share_code', sa.String(length=10), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['history_id'], ['route_history.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shared_code', 'shared_routes', ['share_code'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_shared_code', table_name='shared_routes')
    op.drop_table('shared_routes')
