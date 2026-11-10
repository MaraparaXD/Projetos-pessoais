from datetime import UTC, datetime

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.models import AuthSession, User
from app.infrastructure.security import token_hash

bearer = HTTPBearer(auto_error=False)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
    session = db.get(AuthSession, token_hash(credentials.credentials))
    if not session or session.expires_at <= datetime.now(UTC):
        raise HTTPException(401, "Session expired or invalid", headers={"WWW-Authenticate": "Bearer"})
    user = db.get(User, session.user_id)
    if not user or not user.active:
        raise HTTPException(401, "User unavailable")
    return user


def require_roles(*roles):
    def dependency(user: User = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return user

    return dependency


operator = require_roles("Admin", "Analyst")
admin = require_roles("Admin")
