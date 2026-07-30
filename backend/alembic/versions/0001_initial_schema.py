"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("role in ('admin','viewer')", name="ck_users_role"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_jti", "refresh_tokens", ["jti"], unique=True)

    op.create_table(
        "peers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("encrypted_password", sa.Text(), nullable=False),
        sa.Column("mikrotik_profile", sa.String(length=64), nullable=False),
        sa.Column("service", sa.String(length=16), nullable=False, server_default="pptp"),
        sa.Column("assigned_local_address", sa.String(length=64), nullable=True),
        sa.Column("assigned_remote_address", sa.String(length=64), nullable=True),
        sa.Column("comment", sa.String(length=255), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("mikrotik_secret_id", sa.String(length=32), nullable=True),
        sa.Column("last_seen_online_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_online", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_peers_name", "peers", ["name"], unique=True)
    op.create_index("ix_peers_enabled", "peers", ["enabled"])

    op.create_table(
        "peer_status_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "peer_id", sa.Integer(), sa.ForeignKey("peers.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("is_online", sa.Boolean(), nullable=False),
        sa.Column("uptime_seconds", sa.Integer(), nullable=True),
        sa.Column("caller_id", sa.String(length=64), nullable=True),
        sa.Column("remote_address", sa.String(length=64), nullable=True),
        sa.Column("tx_bytes", sa.BigInteger(), nullable=True),
        sa.Column("rx_bytes", sa.BigInteger(), nullable=True),
    )
    op.create_index("ix_peer_status_snapshots_peer_id", "peer_status_snapshots", ["peer_id"])
    op.create_index("ix_peer_status_snapshots_timestamp", "peer_status_snapshots", ["timestamp"])
    op.create_index(
        "ix_snapshot_peer_ts", "peer_status_snapshots", ["peer_id", "timestamp"]
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "peer_id",
            sa.Integer(),
            sa.ForeignKey("peers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "acknowledged_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_alerts_peer_id", "alerts", ["peer_id"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])
    op.create_index(
        "ix_alerts_unresolved",
        "alerts",
        ["type", "peer_id"],
        postgresql_where=sa.text("resolved_at IS NULL"),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column(
            "target_peer_id",
            sa.Integer(),
            sa.ForeignKey("peers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("before_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True),
        sa.Column("after_json", sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_audit_log_timestamp", "audit_log", ["timestamp"])

    op.create_table(
        "router_config",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("host", sa.String(length=255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("api_user", sa.String(length=64), nullable=False),
        sa.Column("encrypted_secret", sa.Text(), nullable=False),
        sa.Column("protocol", sa.String(length=16), nullable=False, server_default="librouteros"),
        sa.Column("verify_ssl", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "backup_before_bulk_ops", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "notification_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("telegram_bot_token_encrypted", sa.Text(), nullable=True),
        sa.Column("telegram_chat_id", sa.String(length=64), nullable=True),
        sa.Column("smtp_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("smtp_host", sa.String(length=255), nullable=True),
        sa.Column("smtp_port", sa.Integer(), nullable=True),
        sa.Column("smtp_username", sa.String(length=255), nullable=True),
        sa.Column("smtp_password_encrypted", sa.Text(), nullable=True),
        sa.Column("smtp_from_address", sa.String(length=255), nullable=True),
        sa.Column("smtp_to_address", sa.String(length=255), nullable=True),
        sa.Column("smtp_use_tls", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("offline_threshold_minutes", sa.Integer(), nullable=False, server_default="10"),
        sa.Column(
            "router_unreachable_realert_minutes",
            sa.Integer(),
            nullable=False,
            server_default="30",
        ),
        sa.Column("snapshot_retention_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("notification_settings")
    op.drop_table("router_config")
    op.drop_table("audit_log")
    op.drop_index("ix_alerts_unresolved", table_name="alerts")
    op.drop_table("alerts")
    op.drop_table("peer_status_snapshots")
    op.drop_table("peers")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
