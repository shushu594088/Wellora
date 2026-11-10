"""Create the initial test-version account and profile tables."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("accounts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(32), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_accounts_username", "accounts", ["username"], unique=True)
    op.create_table("sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("account_id", sa.String(36), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_sessions_account_id", "sessions", ["account_id"])
    op.create_table("profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_account_id", sa.String(36), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("birth_date", sa.Date()),
        sa.Column("version", sa.Integer(), nullable=False),
    )
    op.create_index("ix_profiles_owner_account_id", "profiles", ["owner_account_id"], unique=True)
    op.create_table("login_throttles",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("failures", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("blocked_until", sa.DateTime(timezone=True)),
    )


def downgrade():
    op.drop_table("login_throttles")
    op.drop_table("profiles")
    op.drop_table("sessions")
    op.drop_table("accounts")
