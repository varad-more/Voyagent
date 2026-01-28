"""init tables

Revision ID: 0001
Revises: 
Create Date: 2026-01-28 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "external_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cache_key", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_external_cache_cache_key", "external_cache", ["cache_key"], unique=True)
    op.create_index("ix_external_cache_source", "external_cache", ["source"])
    op.create_index("ix_external_cache_expires_at", "external_cache", ["expires_at"])
    op.create_index("ix_external_cache_created_at", "external_cache", ["created_at"])

    op.create_table(
        "itineraries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("request_json", sa.JSON(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_itineraries_status", "itineraries", ["status"])
    op.create_index("ix_itineraries_created_at", "itineraries", ["created_at"])
    op.create_index("ix_itineraries_updated_at", "itineraries", ["updated_at"])

    op.create_table(
        "agent_traces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("itinerary_id", sa.Integer(), nullable=False),
        sa.Column("agent_name", sa.String(length=64), nullable=False),
        sa.Column("step_name", sa.String(length=128), nullable=False),
        sa.Column("input_json", sa.JSON(), nullable=True),
        sa.Column("output_json", sa.JSON(), nullable=True),
        sa.Column("issues", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["itinerary_id"], ["itineraries.id"]),
    )
    op.create_index("ix_agent_traces_itinerary_id", "agent_traces", ["itinerary_id"])
    op.create_index("ix_agent_traces_agent_name", "agent_traces", ["agent_name"])
    op.create_index("ix_agent_traces_step_name", "agent_traces", ["step_name"])
    op.create_index("ix_agent_traces_created_at", "agent_traces", ["created_at"])


def downgrade() -> None:
    op.drop_table("agent_traces")
    op.drop_table("itineraries")
    op.drop_table("external_cache")
