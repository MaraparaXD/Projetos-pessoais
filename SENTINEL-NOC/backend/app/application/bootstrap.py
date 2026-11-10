from sqlalchemy import select

from app.application.audit import audit
from app.core.config import get_settings
from app.infrastructure.models import Integration, Role, User
from app.infrastructure.security import encrypt_secret, password_hasher


def bootstrap(db):
    settings = get_settings()
    for role in ("Admin", "Analyst", "Viewer"):
        if not db.get(Role, role):
            db.add(Role(name=role))
    db.flush()
    if settings.bootstrap_admin_email and settings.bootstrap_admin_password:
        if len(settings.bootstrap_admin_password) < 12:
            raise ValueError("Bootstrap password must be at least 12 characters")
        email = settings.bootstrap_admin_email.strip().lower()
        if not db.scalar(select(User).where(User.email == email)):
            user = User(
                email=email,
                name="Administrador",
                role="Admin",
                password_hash=password_hasher.hash(settings.bootstrap_admin_password),
            )
            db.add(user)
            db.flush()
            audit(db, "user.bootstrap", user.id)
    if settings.bootstrap_webhook_secret:
        if len(settings.bootstrap_webhook_secret) < 32:
            raise ValueError("Webhook secret must be at least 32 characters")
        if not db.scalar(select(Integration).where(Integration.name == "Laboratório Checkmk")):
            integration = Integration(
                name="Laboratório Checkmk",
                synthetic=True,
                webhook_secret=encrypt_secret(settings.bootstrap_webhook_secret),
            )
            db.add(integration)
            db.flush()
            audit(db, "integration.bootstrap", integration.id)
    db.commit()
