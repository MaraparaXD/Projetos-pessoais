"""Cria o esquema inicial de eventos e incidentes."""

from alembic import op
import sqlalchemy as sa

import app.infrastructure.database

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "correlation_scopes",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("last_observed_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=True),
        sa.Column("last_state", sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_table(
        "integrations",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("webhook_secret", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("synthetic", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "roles",
        sa.Column("name", sa.String(length=16), nullable=False),
        sa.CheckConstraint("name IN ('Admin','Analyst','Viewer')", name="ck_role_name"),
        sa.PrimaryKeyConstraint("name"),
    )
    op.create_table(
        "hosts",
        sa.Column("integration_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=253), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["integration_id"],
            ["integrations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_id", "name", name="uq_host_integration_name"),
    )
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["role"],
            ["roles.name"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "audit_logs",
        sa.Column("actor_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_created", "audit_logs", ["created_at"], unique=False)
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_table(
        "auth_sessions",
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("expires_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token_hash"),
    )
    op.create_index(op.f("ix_auth_sessions_expires_at"), "auth_sessions", ["expires_at"], unique=False)
    op.create_index(op.f("ix_auth_sessions_user_id"), "auth_sessions", ["user_id"], unique=False)
    op.create_table(
        "services",
        sa.Column("host_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["host_id"],
            ["hosts.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("host_id", "name", name="uq_service_host_name"),
    )
    op.create_table(
        "incidents",
        sa.Column("integration_id", sa.String(length=36), nullable=False),
        sa.Column("host_id", sa.String(length=36), nullable=False),
        sa.Column("service_id", sa.String(length=36), nullable=True),
        sa.Column("host_name", sa.String(length=253), nullable=False),
        sa.Column("service_name", sa.String(length=200), nullable=True),
        sa.Column("event_type", sa.String(length=10), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("severity", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("scope_key", sa.String(length=64), nullable=False),
        sa.Column("active_scope", sa.String(length=64), nullable=True),
        sa.Column("assignee_id", sa.String(length=36), nullable=True),
        sa.Column("last_seen_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=False),
        sa.Column("updated_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=True),
        sa.Column("flapping", sa.Boolean(), nullable=False),
        sa.Column("reopen_count", sa.Integer(), nullable=False),
        sa.Column("synthetic", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(status IN ('OPEN','ACKNOWLEDGED','INVESTIGATING') AND active_scope IS NOT NULL AND active_scope = scope_key) OR (status IN ('RESOLVED','CLOSED') AND active_scope IS NULL)",
            name="ck_incident_active_scope",
        ),
        sa.CheckConstraint("event_type IN ('HOST','SERVICE')", name="ck_incident_type"),
        sa.CheckConstraint("severity IN ('WARN','CRIT','UNKNOWN')", name="ck_incident_severity"),
        sa.CheckConstraint(
            "status IN ('OPEN','ACKNOWLEDGED','INVESTIGATING','RESOLVED','CLOSED')", name="ck_incident_status"
        ),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["host_id"],
            ["hosts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["integration_id"],
            ["integrations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("active_scope"),
    )
    op.create_index("ix_incident_created", "incidents", ["created_at"], unique=False)
    op.create_index(op.f("ix_incidents_integration_id"), "incidents", ["integration_id"], unique=False)
    op.create_index(op.f("ix_incidents_scope_key"), "incidents", ["scope_key"], unique=False)
    op.create_index(op.f("ix_incidents_status"), "incidents", ["status"], unique=False)
    op.create_table(
        "monitoring_events",
        sa.Column("integration_id", sa.String(length=36), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("scope_key", sa.String(length=64), nullable=False),
        sa.Column("host_id", sa.String(length=36), nullable=False),
        sa.Column("service_id", sa.String(length=36), nullable=True),
        sa.Column("host_name", sa.String(length=253), nullable=False),
        sa.Column("service_name", sa.String(length=200), nullable=True),
        sa.Column("event_type", sa.String(length=10), nullable=False),
        sa.Column("state", sa.String(length=10), nullable=False),
        sa.Column("output", sa.Text(), nullable=False),
        sa.Column("observed_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=False),
        sa.Column("out_of_order", sa.Boolean(), nullable=False),
        sa.Column("synthetic", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=False),
        sa.CheckConstraint("event_type IN ('HOST','SERVICE')", name="ck_event_type"),
        sa.CheckConstraint("state IN ('OK','WARN','CRIT','UNKNOWN','RECOVERY')", name="ck_event_state"),
        sa.ForeignKeyConstraint(
            ["host_id"],
            ["hosts.id"],
        ),
        sa.ForeignKeyConstraint(
            ["integration_id"],
            ["integrations.id"],
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_id", "external_id", name="uq_event_integration_external"),
    )
    op.create_index("ix_event_created", "monitoring_events", ["created_at"], unique=False)
    op.create_index(
        "ix_event_scope_observed", "monitoring_events", ["scope_key", "observed_at"], unique=False
    )
    op.create_table(
        "incident_comments",
        sa.Column("incident_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", app.infrastructure.database.UTCDateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_incident_comments_incident_id"), "incident_comments", ["incident_id"], unique=False
    )
    op.create_table(
        "incident_events",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("incident_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["monitoring_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["incident_id"],
            ["incidents.id"],
        ),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(op.f("ix_incident_events_incident_id"), "incident_events", ["incident_id"], unique=False)


def downgrade():

    op.drop_index(op.f("ix_incident_events_incident_id"), table_name="incident_events")
    op.drop_table("incident_events")
    op.drop_index(op.f("ix_incident_comments_incident_id"), table_name="incident_comments")
    op.drop_table("incident_comments")
    op.drop_index("ix_event_scope_observed", table_name="monitoring_events")
    op.drop_index("ix_event_created", table_name="monitoring_events")
    op.drop_table("monitoring_events")
    op.drop_index(op.f("ix_incidents_status"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_scope_key"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_integration_id"), table_name="incidents")
    op.drop_index("ix_incident_created", table_name="incidents")
    op.drop_table("incidents")
    op.drop_table("services")
    op.drop_index(op.f("ix_auth_sessions_user_id"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_expires_at"), table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_index("ix_audit_created", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_table("users")
    op.drop_table("hosts")
    op.drop_table("roles")
    op.drop_table("integrations")
    op.drop_table("correlation_scopes")
