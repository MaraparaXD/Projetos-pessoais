import hashlib
import json
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.application.audit import audit
from app.core.config import get_settings
from app.domain.lifecycle import ACTIVE, HEALTHY, count_transitions
from app.infrastructure.database import utcnow
from app.infrastructure.models import (
    CorrelationScope,
    Host,
    Incident,
    IncidentEvent,
    MonitoringEvent,
    Service,
)
from app.infrastructure.security import redact_output


def lock_scope(db, key):
    insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    db.execute(insert(CorrelationScope).values(key=key).on_conflict_do_nothing(index_elements=["key"]))
    return db.scalar(select(CorrelationScope).where(CorrelationScope.key == key).with_for_update())


def upsert_resource(db, model, values, keys):
    insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    db.execute(insert(model).values(**values).on_conflict_do_nothing(index_elements=keys))
    return db.scalar(select(model).filter_by(**values))


def ingest(db, integration, event):
    settings = get_settings()
    key = hashlib.sha256(
        json.dumps(
            [integration.id, event.host.lower(), event.service, event.event_type], separators=(",", ":")
        ).encode()
    ).hexdigest()
    scope = lock_scope(db, key)

    lock_scope(db, hashlib.sha256(f"id:{integration.id}:{event.external_id}".encode()).hexdigest())
    fingerprint = hashlib.sha256(event.model_dump_json().encode()).hexdigest()
    duplicate = db.scalar(
        select(MonitoringEvent).where(
            MonitoringEvent.integration_id == integration.id, MonitoringEvent.external_id == event.external_id
        )
    )
    if duplicate:
        if duplicate.payload_hash != fingerprint:
            raise HTTPException(409, "external_id already used with a different payload")
        incident_id = db.scalar(
            select(IncidentEvent.incident_id).where(IncidentEvent.event_id == duplicate.id)
        )
        return {"event_id": duplicate.id, "incident_id": incident_id, "duplicate": True}

    host = upsert_resource(
        db, Host, {"integration_id": integration.id, "name": event.host.lower()}, ["integration_id", "name"]
    )
    service = (
        upsert_resource(db, Service, {"host_id": host.id, "name": event.service}, ["host_id", "name"])
        if event.service
        else None
    )
    late = scope.last_observed_at is not None and event.observed_at <= scope.last_observed_at
    record = MonitoringEvent(
        integration_id=integration.id,
        external_id=event.external_id,
        payload_hash=fingerprint,
        scope_key=key,
        host_id=host.id,
        service_id=service.id if service else None,
        host_name=host.name,
        service_name=event.service,
        event_type=event.event_type,
        state=event.state,
        output=redact_output(event.output),
        observed_at=event.observed_at,
        out_of_order=late,
        synthetic=integration.synthetic,
    )
    db.add(record)
    db.flush()
    incident = db.scalar(
        select(Incident).where(Incident.scope_key == key).order_by(Incident.created_at.desc()).limit(1)
    )
    now = utcnow()
    if not late:
        scope.last_observed_at, scope.last_state = event.observed_at, event.state
        recent_states = list(
            db.scalars(
                select(MonitoringEvent.state)
                .where(
                    MonitoringEvent.scope_key == key,
                    MonitoringEvent.observed_at
                    >= event.observed_at - timedelta(seconds=settings.flapping_window_seconds),
                    MonitoringEvent.observed_at <= event.observed_at,
                    MonitoringEvent.out_of_order.is_(False),
                )
                .order_by(MonitoringEvent.observed_at)
            )
        )
        flapping = count_transitions(recent_states) >= settings.flapping_threshold
        if event.state not in HEALTHY:
            if (
                incident
                and incident.status == "RESOLVED"
                and (now - incident.resolved_at <= timedelta(seconds=settings.reopen_window_seconds))
            ):
                incident.status, incident.active_scope = "OPEN", key
                incident.resolved_at = None
                incident.reopen_count += 1
                audit(db, "incident.reopened", incident.id, reason="problem_in_reopen_window")
            elif not incident or incident.status not in ACTIVE:
                incident = Incident(
                    integration_id=integration.id,
                    host_id=host.id,
                    service_id=service.id if service else None,
                    host_name=host.name,
                    service_name=event.service,
                    event_type=event.event_type,
                    title=f"{host.name} / {event.service or 'Disponibilidade do host'}",
                    severity=event.state,
                    status="OPEN",
                    scope_key=key,
                    active_scope=key,
                    last_seen_at=event.observed_at,
                    synthetic=integration.synthetic,
                )
                db.add(incident)
                db.flush()
                audit(db, "incident.created", incident.id, event_id=record.id)
            incident.severity = event.state
        elif incident and incident.status in ACTIVE:
            incident.status, incident.active_scope, incident.resolved_at = "RESOLVED", None, now
            audit(db, "incident.resolved", incident.id, reason="monitoring_recovery", event_id=record.id)
        if incident:
            if incident.flapping != flapping:
                audit(db, "incident.flapping_changed", incident.id, flapping=flapping)
            incident.flapping, incident.last_seen_at, incident.updated_at = flapping, event.observed_at, now
    if incident:
        db.add(IncidentEvent(incident_id=incident.id, event_id=record.id))
    audit(db, "event.ingested", record.id, incident_id=incident.id if incident else None, out_of_order=late)
    db.flush()
    return {"event_id": record.id, "incident_id": incident.id if incident else None, "duplicate": False}
