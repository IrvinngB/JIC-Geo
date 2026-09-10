"""add route_history table

Revision ID: a0133e5a7bdb
Revises: bcd90c388f71
Create Date: 2026-09-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0133e5a7bdb'
down_revision: Union[str, None] = 'bcd90c388f71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'route_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('profile_id', sa.UUID(), nullable=True),
        sa.Column('route_name', sa.String(length=200), nullable=True),
        sa.Column('route_id', sa.String(length=50), nullable=False),
        sa.Column('source_format', sa.String(length=10), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), nullable=False),
        sa.Column('mide_global', sa.Integer(), nullable=True),
        sa.Column('total_distance_km', sa.Float(), nullable=True),
        sa.Column('estimated_time_h', sa.Float(), nullable=True),
        sa.Column('total_kcal', sa.Float(), nullable=True),
        sa.Column('elevation_gain_m', sa.Float(), nullable=True),
        sa.Column('risk_max', sa.Integer(), nullable=True),
        sa.Column('analysis_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_history_user', 'route_history', ['user_id'], unique=False)
    op.create_index('ix_history_created', 'route_history', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_history_created', table_name='route_history')
    op.drop_index('ix_history_user', table_name='route_history')
    op.drop_table('route_history')
