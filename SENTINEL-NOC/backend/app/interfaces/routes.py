import secrets
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from sqlalchemy import extract, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.audit import audit
from app.application.events import ingest
from app.application.incidents import change_status, locked_incident
from app.core.config import get_settings
from app.domain.lifecycle import ACTIVE, IncidentStatus, Severity
from app.infrastructure.database import get_db, utcnow
from app.infrastructure.models import (
    AuditLog,
    AuthSession,
    Host,
    Incident,
    IncidentComment,
    IncidentEvent,
    Integration,
    MonitoringEvent,
    Service,
    User,
)
from app.infrastructure.security import (
    DUMMY_HASH,
    decrypt_secret,
    encrypt_secret,
    password_hasher,
    token_hash,
    verify_signature,
)
from app.interfaces.dependencies import admin, bearer, current_user, operator
from app.interfaces.schemas import (
    AssignmentIn,
    AuditOut,
    CommentIn,
    CommentOut,
    EventIn,
    EventOut,
    IncidentOut,
    IntegrationIn,
    IntegrationOut,
    LoginIn,
    TransitionIn,
    UserIn,
    UserOut,
)

router = APIRouter(prefix="/api")
DB = Annotated[Session, Depends(get_db)]
Limit = Annotated[int, Query(ge=1, le=200)]
Offset = Annotated[int, Query(ge=0)]


def page(db, statement, schema, limit, offset):
    total = db.scalar(select(func.count()).select_from(statement.order_by(None).subquery()))
    rows = db.scalars(statement.limit(limit).offset(offset)).all()
    return {
        "items": [schema.model_validate(row).model_dump(mode="json") for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/auth/login", tags=["auth"])
def login(data: LoginIn, db: DB):
    user = db.scalar(select(User).where(User.email == data.email.strip().lower()))
    valid = password_hasher.verify(data.password, user.password_hash if user else DUMMY_HASH)
    if not valid or not user or not user.active:
        audit(db, "auth.login_failed")
        db.commit()
        raise HTTPException(401, "Invalid email or password")
    token = secrets.token_urlsafe(48)
    db.add(
        AuthSession(
            token_hash=token_hash(token),
            user_id=user.id,
            expires_at=utcnow() + timedelta(hours=get_settings().session_hours),
        )
    )
    audit(db, "auth.login", user.id, user.id)
    db.commit()
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": get_settings().session_hours * 3600,
        "user": UserOut.model_validate(user),
    }


@router.get("/auth/me", response_model=UserOut, tags=["auth"])
def me(user=Depends(current_user)):
    return user


@router.post("/auth/logout", status_code=204, tags=["auth"])
def logout(db: DB, credentials=Depends(bearer), user=Depends(current_user)):
    db.delete(db.get(AuthSession, token_hash(credentials.credentials)))
    audit(db, "auth.logout", user.id, user.id)
    db.commit()
    return Response(status_code=204)


@router.get("/users", response_model=list[UserOut], tags=["users"])
def users(db: DB, _=Depends(operator)):
    return db.scalars(select(User).where(User.active.is_(True)).order_by(User.name).limit(200)).all()


@router.post("/users", response_model=UserOut, status_code=201, tags=["users"])
def create_user(data: UserIn, db: DB, actor=Depends(admin)):
    user = User(
        email=data.email.strip().lower(),
        name=data.name,
        role=data.role,
        password_hash=password_hasher.hash(data.password),
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email already registered") from None
    audit(db, "user.created", user.id, actor.id, role=user.role)
    db.commit()
    return user


@router.get("/integrations", response_model=list[IntegrationOut], tags=["integrations"])
def integrations(db: DB, _=Depends(admin)):
    return db.scalars(select(Integration).order_by(Integration.created_at).limit(200)).all()


@router.post("/integrations", status_code=201, tags=["integrations"])
def create_integration(data: IntegrationIn, db: DB, actor=Depends(admin)):
    secret = secrets.token_urlsafe(48)
    integration = Integration(name=data.name, synthetic=data.synthetic, webhook_secret=encrypt_secret(secret))
    db.add(integration)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Integration name already exists") from None
    audit(db, "integration.created", integration.id, actor.id, synthetic=data.synthetic)
    db.commit()
    return {"integration": IntegrationOut.model_validate(integration), "webhook_secret": secret}


@router.post("/integrations/{integration_id}/rotate-secret", tags=["integrations"])
def rotate_secret(integration_id: str, db: DB, actor=Depends(admin)):
    integration = db.get(Integration, integration_id)
    if not integration:
        raise HTTPException(404, "Integration not found")
    secret = secrets.token_urlsafe(48)
    integration.webhook_secret = encrypt_secret(secret)
    audit(db, "integration.secret_rotated", integration.id, actor.id)
    db.commit()
    return {"webhook_secret": secret}


async def raw_body(request: Request):
    return await request.body()


@router.post("/webhooks/checkmk/{integration_id}", tags=["events"])
def webhook(
    integration_id: str,
    response: Response,
    db: DB,
    body: bytes = Depends(raw_body),
    x_sentinel_timestamp: str = Header(default=""),
    x_sentinel_signature: str = Header(default=""),
):
    integration = db.get(Integration, integration_id)
    if not integration or not integration.enabled:
        raise HTTPException(401, "Invalid webhook authentication")
    verify_signature(
        decrypt_secret(integration.webhook_secret), body, x_sentinel_timestamp, x_sentinel_signature
    )

    try:
        data = EventIn.model_validate_json(body)
    except ValueError:
        raise HTTPException(422, "Invalid event payload; consult EventIn in /openapi.json") from None
    result = ingest(db, integration, data)
    db.commit()
    response.status_code = 200 if result["duplicate"] else 201
    return result


@router.get("/events", tags=["events"])
def events(
    db: DB,
    limit: Limit = 50,
    offset: Offset = 0,
    state: Severity | None = None,
    host: str = Query(default="", max_length=253),
    _=Depends(current_user),
):
    statement = select(MonitoringEvent).order_by(MonitoringEvent.created_at.desc())
    if state:
        statement = statement.where(MonitoringEvent.state == state)
    if host:
        statement = statement.where(MonitoringEvent.host_name.icontains(host, autoescape=True))
    return page(db, statement, EventOut, limit, offset)


@router.get("/incidents", tags=["incidents"])
def incidents(
    db: DB,
    limit: Limit = 50,
    offset: Offset = 0,
    status: IncidentStatus | None = None,
    severity: Severity | None = None,
    host: str = Query(default="", max_length=253),
    _=Depends(current_user),
):
    statement = select(Incident).order_by(Incident.updated_at.desc())
    if status:
        statement = statement.where(Incident.status == status)
    if severity:
        statement = statement.where(Incident.severity == severity)
    if host:
        statement = statement.where(Incident.host_name.icontains(host, autoescape=True))
    return page(db, statement, IncidentOut, limit, offset)


@router.get("/incidents/{incident_id}", response_model=IncidentOut, tags=["incidents"])
def incident_detail(incident_id: str, db: DB, _=Depends(current_user)):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    return incident


@router.get("/incidents/{incident_id}/events", tags=["incidents"])
def incident_events(incident_id: str, db: DB, limit: Limit = 50, offset: Offset = 0, _=Depends(current_user)):
    if not db.get(Incident, incident_id):
        raise HTTPException(404, "Incident not found")
    statement = (
        select(MonitoringEvent)
        .join(IncidentEvent)
        .where(IncidentEvent.incident_id == incident_id)
        .order_by(MonitoringEvent.observed_at.desc())
    )
    return page(db, statement, EventOut, limit, offset)


@router.patch("/incidents/{incident_id}/status", response_model=IncidentOut, tags=["incidents"])
def transition(incident_id: str, data: TransitionIn, db: DB, actor=Depends(operator)):
    incident = locked_incident(db, incident_id)
    change_status(db, incident, data.status, actor.id)
    db.commit()
    return incident


@router.patch("/incidents/{incident_id}/assignment", response_model=IncidentOut, tags=["incidents"])
def assign(incident_id: str, data: AssignmentIn, db: DB, actor=Depends(operator)):
    incident = locked_incident(db, incident_id)
    if data.assignee_id:
        assignee = db.get(User, data.assignee_id)
        if not assignee or not assignee.active or assignee.role not in {"Admin", "Analyst"}:
            raise HTTPException(422, "Assignee must be an active Admin or Analyst")
    incident.assignee_id, incident.updated_at = data.assignee_id, utcnow()
    audit(db, "incident.assigned", incident.id, actor.id, assignee_id=data.assignee_id)
    db.commit()
    return incident


@router.get("/incidents/{incident_id}/comments", tags=["incidents"])
def comments(incident_id: str, db: DB, limit: Limit = 50, offset: Offset = 0, _=Depends(current_user)):
    if not db.get(Incident, incident_id):
        raise HTTPException(404, "Incident not found")
    return page(
        db,
        select(IncidentComment)
        .where(IncidentComment.incident_id == incident_id)
        .order_by(IncidentComment.created_at.desc()),
        CommentOut,
        limit,
        offset,
    )


@router.post(
    "/incidents/{incident_id}/comments", response_model=CommentOut, status_code=201, tags=["incidents"]
)
def comment(incident_id: str, data: CommentIn, db: DB, actor=Depends(operator)):
    if not db.get(Incident, incident_id):
        raise HTTPException(404, "Incident not found")
    entry = IncidentComment(incident_id=incident_id, user_id=actor.id, body=data.body)
    db.add(entry)
    db.flush()
    audit(db, "incident.commented", incident_id, actor.id, comment_id=entry.id)
    db.commit()
    return entry


@router.get("/hosts", tags=["inventory"])
def hosts(db: DB, limit: Limit = 50, offset: Offset = 0, _=Depends(current_user)):
    total = db.scalar(select(func.count()).select_from(Host))
    hosts = db.scalars(select(Host).order_by(Host.name).limit(limit).offset(offset)).all()
    ids = [host.id for host in hosts]
    services = db.scalars(select(Service).where(Service.host_id.in_(ids))).all() if ids else []
    return {
        "items": [
            {
                "id": h.id,
                "name": h.name,
                "integration_id": h.integration_id,
                "services": [{"id": s.id, "name": s.name} for s in services if s.host_id == h.id],
            }
            for h in hosts
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/audit", tags=["audit"])
def audit_list(
    db: DB,
    limit: Limit = 50,
    offset: Offset = 0,
    entity_id: str | None = Query(default=None, max_length=128),
    _=Depends(admin),
):
    statement = select(AuditLog).order_by(AuditLog.created_at.desc())
    if entity_id:
        statement = statement.where(AuditLog.entity_id == entity_id)
    return page(db, statement, AuditOut, limit, offset)


@router.get("/dashboard", tags=["dashboard"])
def dashboard(db: DB, _=Depends(current_user)):
    now = utcnow()
    since = now - timedelta(hours=24)
    active = Incident.status.in_(ACTIVE)
    by_severity = dict(
        db.execute(
            select(MonitoringEvent.state, func.count())
            .where(MonitoringEvent.created_at >= since)
            .group_by(MonitoringEvent.state)
        ).all()
    )
    by_status = dict(db.execute(select(Incident.status, func.count()).group_by(Incident.status)).all())

    def average_seconds(end):
        if db.bind.dialect.name == "postgresql":
            duration = extract("epoch", end - Incident.created_at)
        else:
            duration = (func.julianday(end) - func.julianday(Incident.created_at)) * 86400
        return db.scalar(select(func.avg(duration)).where(end.is_not(None)))

    hour = extract("hour", MonitoringEvent.created_at)
    day = extract("day", MonitoringEvent.created_at)
    trend_counts = {
        (int(d), int(h)): count
        for d, h, count in db.execute(
            select(day, hour, func.count()).where(MonitoringEvent.created_at >= since).group_by(day, hour)
        )
    }
    trend = []

    for i in range(24, -1, -1):
        bucket = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=i)
        trend.append({"hour": bucket.isoformat(), "events": trend_counts.get((bucket.day, bucket.hour), 0)})
    return {
        "generated_at": now,
        "window_hours": 24,
        "open_incidents": db.scalar(select(func.count()).select_from(Incident).where(active)),
        "affected_hosts": db.scalar(select(func.count(func.distinct(Incident.host_id))).where(active)),
        "critical_services": db.scalar(
            select(func.count(func.distinct(Incident.service_id))).where(
                active, Incident.severity == "CRIT", Incident.service_id.is_not(None)
            )
        ),
        "events_24h": sum(by_severity.values()),
        "events_by_severity": by_severity,
        "incidents_by_status": by_status,
        "trend": trend,
        "mean_acknowledge_seconds": average_seconds(Incident.acknowledged_at),
        "mean_resolve_seconds": average_seconds(Incident.resolved_at),
        "synthetic_events": db.scalar(
            select(func.count()).select_from(MonitoringEvent).where(MonitoringEvent.synthetic.is_(True))
        ),
        "total_events": db.scalar(select(func.count()).select_from(MonitoringEvent)),
        "notifications": {"enabled": False, "pending": None},
    }


@router.get("/settings", tags=["settings"])
def public_settings(_=Depends(current_user)):
    settings = get_settings()
    return {
        "environment": settings.environment,
        "reopen_window_seconds": settings.reopen_window_seconds,
        "flapping_window_seconds": settings.flapping_window_seconds,
        "flapping_threshold": settings.flapping_threshold,
        "event_retention_days": settings.event_retention_days,
        "audit_retention_days": settings.audit_retention_days,
        "phase": "1–2",
        "ai_enabled": False,
        "automation_enabled": False,
    }
