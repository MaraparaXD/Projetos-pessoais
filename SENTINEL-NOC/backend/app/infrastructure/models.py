import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base, UTCDateTime, utcnow


def new_id():
    return str(uuid.uuid4())


class Identity:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class Role(Base):
    __tablename__ = "roles"
    name: Mapped[str] = mapped_column(String(16), primary_key=True)
    __table_args__ = (CheckConstraint("name IN ('Admin','Analyst','Viewer')", name="ck_role_name"),)


class User(Identity, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(ForeignKey("roles.name"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)


class Integration(Identity, Base):
    __tablename__ = "integrations"
    name: Mapped[str] = mapped_column(String(100), unique=True)
    kind: Mapped[str] = mapped_column(String(30), default="checkmk")
    webhook_secret: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)


class Host(Identity, Base):
    __tablename__ = "hosts"
    integration_id: Mapped[str] = mapped_column(ForeignKey("integrations.id"))
    name: Mapped[str] = mapped_column(String(253))
    __table_args__ = (UniqueConstraint("integration_id", "name", name="uq_host_integration_name"),)


class Service(Identity, Base):
    __tablename__ = "services"
    host_id: Mapped[str] = mapped_column(ForeignKey("hosts.id"))
    name: Mapped[str] = mapped_column(String(200))
    __table_args__ = (UniqueConstraint("host_id", "name", name="uq_service_host_name"),)


class CorrelationScope(Base):
    __tablename__ = "correlation_scopes"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    last_observed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    last_state: Mapped[str | None] = mapped_column(String(10))


class Incident(Identity, Base):
    __tablename__ = "incidents"
    integration_id: Mapped[str] = mapped_column(ForeignKey("integrations.id"), index=True)
    host_id: Mapped[str] = mapped_column(ForeignKey("hosts.id"))
    service_id: Mapped[str | None] = mapped_column(ForeignKey("services.id"))
    host_name: Mapped[str] = mapped_column(String(253))
    service_name: Mapped[str | None] = mapped_column(String(200))
    event_type: Mapped[str] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(500))
    severity: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="OPEN", index=True)
    scope_key: Mapped[str] = mapped_column(String(64), index=True)
    active_scope: Mapped[str | None] = mapped_column(String(64), unique=True)
    assignee_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    acknowledged_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    flapping: Mapped[bool] = mapped_column(Boolean, default=False)
    reopen_count: Mapped[int] = mapped_column(Integer, default=0)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (
        CheckConstraint(
            "status IN ('OPEN','ACKNOWLEDGED','INVESTIGATING','RESOLVED','CLOSED')", name="ck_incident_status"
        ),
        CheckConstraint("severity IN ('WARN','CRIT','UNKNOWN')", name="ck_incident_severity"),
        CheckConstraint("event_type IN ('HOST','SERVICE')", name="ck_incident_type"),
        CheckConstraint(
            "(status IN ('OPEN','ACKNOWLEDGED','INVESTIGATING') AND active_scope IS NOT NULL AND active_scope = scope_key) OR (status IN ('RESOLVED','CLOSED') AND active_scope IS NULL)",
            name="ck_incident_active_scope",
        ),
        Index("ix_incident_created", "created_at"),
    )


class MonitoringEvent(Identity, Base):
    __tablename__ = "monitoring_events"
    integration_id: Mapped[str] = mapped_column(ForeignKey("integrations.id"))
    external_id: Mapped[str] = mapped_column(String(128))
    payload_hash: Mapped[str] = mapped_column(String(64))
    scope_key: Mapped[str] = mapped_column(String(64))
    host_id: Mapped[str] = mapped_column(ForeignKey("hosts.id"))
    service_id: Mapped[str | None] = mapped_column(ForeignKey("services.id"))
    host_name: Mapped[str] = mapped_column(String(253))
    service_name: Mapped[str | None] = mapped_column(String(200))
    event_type: Mapped[str] = mapped_column(String(10))
    state: Mapped[str] = mapped_column(String(10))
    output: Mapped[str] = mapped_column(Text)
    observed_at: Mapped[datetime] = mapped_column(UTCDateTime)
    out_of_order: Mapped[bool] = mapped_column(Boolean, default=False)
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (
        UniqueConstraint("integration_id", "external_id", name="uq_event_integration_external"),
        CheckConstraint("state IN ('OK','WARN','CRIT','UNKNOWN','RECOVERY')", name="ck_event_state"),
        CheckConstraint("event_type IN ('HOST','SERVICE')", name="ck_event_type"),
        Index("ix_event_scope_observed", "scope_key", "observed_at"),
        Index("ix_event_created", "created_at"),
    )


class IncidentEvent(Base):
    __tablename__ = "incident_events"
    event_id: Mapped[str] = mapped_column(
        ForeignKey("monitoring_events.id", ondelete="CASCADE"), primary_key=True
    )
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)


class IncidentComment(Identity, Base):
    __tablename__ = "incident_comments"
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)


class AuditLog(Identity, Base):
    __tablename__ = "audit_logs"
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(128), index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    correlation_id: Mapped[str] = mapped_column(String(64))
    __table_args__ = (Index("ix_audit_created", "created_at"),)
