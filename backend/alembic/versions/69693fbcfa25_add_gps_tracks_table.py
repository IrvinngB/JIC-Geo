"""add gps_tracks table

Revision ID: 69693fbcfa25
Revises: 158d9b339665
Create Date: 2026-09-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = '69693fbcfa25'
down_revision: Union[str, None] = '158d9b339665'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'gps_tracks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('history_id', sa.UUID(), nullable=False),
        sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='LINESTRINGZ', srid=4326), nullable=True),
        sa.Column('total_distance_m', sa.Float(), nullable=True),
        sa.Column('duration_s', sa.Integer(), nullable=True),
        sa.Column('avg_speed_kmh', sa.Float(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['history_id'], ['route_history.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_gps_tracks_geom', 'gps_tracks', ['geom'], unique=False, postgresql_using='gist')


def downgrade() -> None:
    op.drop_index('idx_gps_tracks_geom', table_name='gps_tracks')
    op.drop_table('gps_tracks')
