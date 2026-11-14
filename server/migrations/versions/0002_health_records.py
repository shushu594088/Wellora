"""Add versioned, attributed health records and create idempotency keys."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("health_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("profile_id", sa.String(36), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("value_state", sa.String(16), nullable=False),
        sa.Column("content", sa.Text()),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_file_id", sa.String(36)),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("version", sa.Integer(), nullable=False),
    )
    op.create_index("ix_health_records_profile_id", "health_records", ["profile_id"])
    op.create_index("ix_health_records_actor_id", "health_records", ["actor_id"])

    op.create_table("idempotency_keys",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope", sa.String(96), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(36), sa.ForeignKey("health_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("response_snapshot", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("account_id", "scope", "key", name="uq_idempotency_account_scope_key"),
    )
    op.create_index("ix_idempotency_keys_account_id", "idempotency_keys", ["account_id"])


def downgrade():
    op.drop_table("idempotency_keys")
    op.drop_table("health_records")
