"""Inicia uma API isolada para os testes de navegador."""

import base64
import os
import secrets
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
os.chdir(root / "backend")
sys.path.insert(0, str(root / "backend"))
db_path = Path(tempfile.mkdtemp(prefix="sentinel-e2e-")) / "e2e.db"
os.environ.update(
    {
        "ENVIRONMENT": "test",
        "DATABASE_URL": f"sqlite:///{db_path.as_posix()}",
        "REDIS_URL": "",
        "BOOTSTRAP_ADMIN_EMAIL": "e2e@test.local",
        "BOOTSTRAP_ADMIN_PASSWORD": "e2e-only-strong-password",
        "BOOTSTRAP_WEBHOOK_SECRET": "e2e-only-synthetic-webhook-secret-32chars",
        "INTEGRATION_ENCRYPTION_KEY": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
    }
)

import uvicorn  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

command.upgrade(Config("alembic.ini"), "head")
uvicorn.run("app.main:app", host="127.0.0.1", port=8001, access_log=False)
