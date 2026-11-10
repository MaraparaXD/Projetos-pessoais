import argparse
import getpass
from datetime import timedelta

from sqlalchemy import delete, select

from app.application.audit import audit
from app.infrastructure.database import SessionLocal, utcnow
from app.infrastructure.models import AuditLog, AuthSession, IncidentEvent, MonitoringEvent, Role, User
from app.infrastructure.security import password_hasher


def main():
    parser = argparse.ArgumentParser(description="SENTINEL administration; run against the intended database")
    commands = parser.add_subparsers(dest="command", required=True)
    user = commands.add_parser("create-user")
    user.add_argument("--email", required=True)
    user.add_argument("--name", default="Operador")
    user.add_argument("--role", choices=["Admin", "Analyst", "Viewer"], default="Admin")
    commands.add_parser("retention")
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.command == "create-user":
            from app.interfaces.schemas import UserIn

            password = getpass.getpass("Password (12+ characters): ")
            if password != getpass.getpass("Confirm password: "):
                raise SystemExit("Passwords do not match")
            data = UserIn(email=args.email, name=args.name, role=args.role, password=password)
            if db.scalar(select(User).where(User.email == data.email.strip().lower())):
                raise SystemExit("User already exists")
            for name in ("Admin", "Analyst", "Viewer"):
                if not db.get(Role, name):
                    db.add(Role(name=name))
            db.flush()
            user = User(
                email=data.email.strip().lower(),
                name=data.name,
                role=data.role,
                password_hash=password_hasher.hash(password),
            )
            db.add(user)
            db.flush()
            audit(db, "user.provisioned", user.id, role=user.role)
            db.commit()
            print("User created")
        elif args.command == "retention":
            from app.core.config import get_settings

            settings = get_settings()
            cutoff = utcnow() - timedelta(days=settings.event_retention_days)

            from app.domain.lifecycle import ACTIVE
            from app.infrastructure.models import Incident

            active_ids = select(IncidentEvent.event_id).join(Incident).where(Incident.status.in_(ACTIVE))
            result = db.execute(
                delete(MonitoringEvent).where(
                    MonitoringEvent.created_at < cutoff, MonitoringEvent.id.not_in(active_ids)
                )
            )
            events_deleted = result.rowcount
            db.execute(delete(AuthSession).where(AuthSession.expires_at < utcnow()))
            result = db.execute(
                delete(AuditLog).where(
                    AuditLog.created_at < utcnow() - timedelta(days=settings.audit_retention_days)
                )
            )
            audit(db, "retention.executed", events_deleted=events_deleted, audit_deleted=result.rowcount)
            db.commit()
            print(f"Deleted {events_deleted} expired events; active incident history preserved")


if __name__ == "__main__":
    main()
