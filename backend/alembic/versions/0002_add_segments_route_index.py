"""add index on segments.route_id

Revision ID: 0002_add_segments_route_index
Revises: 0001_initial
Create Date: 2026-06-09

Adds a B-tree index on segments(route_id) so route-scoped joins and
WHERE clauses do not degrade to full table scans as segment count grows.
"""

from __future__ import annotations

from alembic import op

revision: str = "0002_add_segments_route_index"
down_revision: str = "0001_initial"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_index("idx_segments_route", "segments", ["route_id"])


def downgrade() -> None:
    op.drop_index("idx_segments_route", table_name="segments")
