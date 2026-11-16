"""Record private OCR budget reservations and idempotency."""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ocr_calls",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("reserved_rmb", sa.Numeric(10, 4), nullable=False),
        sa.Column("provider_sid", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ocr_calls_request_fingerprint", "ocr_calls", ["request_fingerprint"], unique=True)
    op.create_index("ix_ocr_calls_created_at", "ocr_calls", ["created_at"])


def downgrade():
    op.drop_table("ocr_calls")
