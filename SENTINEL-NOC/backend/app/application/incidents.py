from fastapi import HTTPException
from sqlalchemy import select

from app.application.audit import audit
from app.application.events import lock_scope
from app.domain.lifecycle import ACTIVE, transition_allowed
from app.infrastructure.database import utcnow
from app.infrastructure.models import Incident


def locked_incident(db, incident_id):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    lock_scope(db, incident.scope_key)
    db.refresh(incident)
    return incident


def change_status(db, incident, target, actor_id):
    if not transition_allowed(incident.status, target):
        raise HTTPException(409, f"Transition {incident.status} → {target} is not allowed")
    if target in ACTIVE:
        other = db.scalar(
            select(Incident.id).where(Incident.active_scope == incident.scope_key, Incident.id != incident.id)
        )
        if other:
            raise HTTPException(409, "Another active incident already covers this resource")
    previous = incident.status
    now = utcnow()
    incident.status, incident.updated_at = target, now
    incident.active_scope = incident.scope_key if target in ACTIVE else None
    if target in {"ACKNOWLEDGED", "INVESTIGATING"} and not incident.acknowledged_at:
        incident.acknowledged_at = now
    if target == "RESOLVED":
        incident.resolved_at = now
    if target == "OPEN":
        incident.resolved_at = None
        incident.reopen_count += 1
    audit(db, "incident.status_changed", incident.id, actor_id, previous=previous, status=target)
