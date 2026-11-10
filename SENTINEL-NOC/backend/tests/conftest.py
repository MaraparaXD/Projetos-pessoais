import base64
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.infrastructure.database import Base, get_db, make_engine
from app.infrastructure.models import Integration, Role, User
from app.infrastructure.security import encrypt_secret, password_hasher
from scripts.simulate_checkmk import signed_payload

SECRET = "synthetic-test-secret-with-more-than-32-characters"


@pytest.fixture
def env(tmp_path, monkeypatch):
    url = os.getenv("TEST_DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    if url.startswith("postgresql") and not url.split("?", 1)[0].endswith("_test"):
        pytest.fail("TEST_DATABASE_URL must target a dedicated database ending in _test")
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "")
    monkeypatch.setenv("BOOTSTRAP_WEBHOOK_SECRET", "")
    monkeypatch.setenv("INTEGRATION_ENCRYPTION_KEY", base64.urlsafe_b64encode(b"s" * 32).decode())
    get_settings.cache_clear()
    cfg = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    cfg.set_main_option("script_location", str(Path(__file__).parents[1] / "migrations"))
    command.upgrade(cfg, "head")
    engine = make_engine(url)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(delete(table))
        for name in ("Admin", "Analyst", "Viewer"):
            db.add(Role(name=name))
        db.flush()
        password_hash = password_hasher.hash("test-password-strong")
        for name in ("Admin", "Analyst", "Viewer"):
            db.add(
                User(email=f"{name.lower()}@test.local", name=name, role=name, password_hash=password_hash)
            )
        integration = Integration(name="Test lab", webhook_secret=encrypt_secret(SECRET), synthetic=True)
        db.add(integration)
        db.commit()
        integration_id = integration.id
    from app import main

    monkeypatch.setattr(main, "engine", engine)
    app = main.create_app(with_bootstrap=False)

    def test_db():
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    with TestClient(app) as client:
        yield client, factory, integration_id
    engine.dispose()
    get_settings.cache_clear()


@pytest.fixture
def client(env):
    return env[0]


@pytest.fixture
def headers(client):
    def for_role(role="admin"):
        response = client.post(
            "/api/auth/login", json={"email": f"{role}@test.local", "password": "test-password-strong"}
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return for_role


@pytest.fixture
def send(env):
    def do(payload, integration_id=None, secret=SECRET):
        body, signed = signed_payload(payload, secret)
        return env[0].post(f"/api/webhooks/checkmk/{integration_id or env[2]}", content=body, headers=signed)

    return do
