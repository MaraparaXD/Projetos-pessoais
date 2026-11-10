from contextvars import ContextVar

from app.infrastructure.models import AuditLog

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="system")


def audit(db, action, entity_id=None, actor_id=None, **details):
    db.add(
        AuditLog(
            action=action,
            entity_id=entity_id,
            actor_id=actor_id,
            details=details,
            correlation_id=correlation_id.get(),
        )
    )
