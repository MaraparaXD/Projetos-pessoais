from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.domain.lifecycle import count_transitions, transition_allowed
from app.infrastructure.database import utcnow
from app.infrastructure.models import AuthSession, Incident, Integration, MonitoringEvent, User
from app.infrastructure.security import encrypt_secret
from scripts.simulate_checkmk import scenario, signed_payload


def payload(state="CRIT", number=0, host="lab-edge-01", service=None):
    return {
        "external_id": f"event-{number}",
        "host": host,
        "service": service,
        "event_type": "SERVICE" if service else "HOST",
        "state": state,
        "output": "Synthetic test",
        "observed_at": (utcnow() - timedelta(seconds=60 - number)).isoformat(),
    }


def test_domain():
    assert count_transitions(["CRIT", "OK", "RECOVERY", "CRIT"]) == 2
    assert transition_allowed("OPEN", "ACKNOWLEDGED")
    assert not transition_allowed("CLOSED", "OPEN")


def test_auth_logout_and_invalid_password(client, headers):
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.post("/api/auth/login", json={"email": "admin@test.local", "password": "wrong"}).status_code
        == 401
    )
    auth = headers()
    assert client.get("/api/auth/me", headers=auth).json()["role"] == "Admin"
    assert client.post("/api/auth/logout", headers=auth).status_code == 204
    assert client.get("/api/auth/me", headers=auth).status_code == 401


def test_expired_and_disabled_sessions(env, headers):
    client, factory, _ = env
    auth = headers()
    with factory() as db:
        session = db.scalar(select(AuthSession))
        session.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.get("/api/auth/me", headers=auth).status_code == 401
    auth = headers()
    with factory() as db:
        db.scalar(select(User).where(User.role == "Admin")).active = False
        db.commit()
    assert client.get("/api/auth/me", headers=auth).status_code == 401


def test_ingest_replay_and_conflict(client, send, headers):
    data = payload()
    first = send(data)
    assert first.status_code == 201, first.text
    replay = send(data)
    assert replay.status_code == 200 and replay.json()["duplicate"]
    assert replay.json()["event_id"] == first.json()["event_id"]
    assert send({**data, "state": "WARN"}).status_code == 409
    auth = headers()
    assert client.get("/api/events", headers=auth).json()["total"] == 1
    assert client.get("/api/incidents", headers=auth).json()["total"] == 1


def test_correlation_and_isolation(client, send, headers):
    a = send(payload(number=0)).json()
    b = send(payload(number=1)).json()
    c = send(payload(number=2, service="Disk")).json()
    d = send(payload(number=3, host="other-host")).json()
    assert a["incident_id"] == b["incident_id"]
    assert len({a["incident_id"], c["incident_id"], d["incident_id"]}) == 3
    assert client.get(f"/api/incidents/{a['incident_id']}/events", headers=headers()).json()["total"] == 2


def test_integration_isolation(env, send):
    _, factory, _ = env
    from tests.conftest import SECRET

    with factory() as db:
        integration = Integration(name="Other", webhook_secret=encrypt_secret(SECRET))
        db.add(integration)
        db.commit()
        other_id = integration.id
    data = payload()
    a = send(data).json()
    b = send(data, integration_id=other_id).json()
    assert a["incident_id"] != b["incident_id"]


def test_recovery_reopen_close_and_new_incident(client, send, headers):
    first = send(payload()).json()["incident_id"]
    send(payload("RECOVERY", 1))
    auth = headers("analyst")
    path = f"/api/incidents/{first}"
    assert client.get(path, headers=auth).json()["status"] == "RESOLVED"
    assert send(payload("CRIT", 2)).json()["incident_id"] == first
    assert client.get(path, headers=auth).json()["reopen_count"] == 1
    assert client.patch(path + "/status", headers=auth, json={"status": "CLOSED"}).status_code == 409
    for status in ("ACKNOWLEDGED", "INVESTIGATING", "RESOLVED", "CLOSED"):
        response = client.patch(path + "/status", headers=auth, json={"status": status})
        assert response.status_code == 200, response.text
    assert send(payload("CRIT", 3)).json()["incident_id"] != first


def test_reopen_window_expiry(env, send):
    _, factory, _ = env
    first = send(payload()).json()["incident_id"]
    send(payload("OK", 1))
    with factory() as db:
        db.get(Incident, first).resolved_at = utcnow() - timedelta(hours=1)
        db.commit()
    assert send(payload("CRIT", 2)).json()["incident_id"] != first


def test_flapping_and_window_expiry(client, send, headers):
    first = None
    for index, state in enumerate(["CRIT", "OK", "CRIT", "OK", "CRIT"]):
        first = send(payload(state, index)).json()["incident_id"]
    assert client.get(f"/api/incidents/{first}", headers=headers()).json()["flapping"] is True


def test_out_of_order_recovery_cannot_resolve(client, send, headers):
    first = send(payload(number=5)).json()["incident_id"]
    assert send(payload("RECOVERY", 1)).status_code == 201
    auth = headers()
    assert client.get(f"/api/incidents/{first}", headers=auth).json()["status"] == "OPEN"
    assert client.get("/api/events", headers=auth).json()["items"][0]["out_of_order"] is True


def test_healthy_without_incident(client, send, headers):
    result = send(payload("OK"))
    assert result.status_code == 201 and result.json()["incident_id"] is None
    assert client.get("/api/incidents", headers=headers()).json()["total"] == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("host", ""),
        ("state", "DOWN"),
        ("service", "Disk"),
        ("observed_at", "2026-01-01T00:00:00"),
        ("external_id", ""),
    ],
)
def test_validation(send, field, value):
    assert send({**payload(), field: value}).status_code == 422


def test_webhook_security(env, send):
    client, _, integration_id = env
    assert send(payload(), secret="wrong").status_code == 401
    body, signed = signed_payload(payload(), "wrong", timestamp=1)
    assert (
        client.post(f"/api/webhooks/checkmk/{integration_id}", content=body, headers=signed).status_code
        == 401
    )
    assert client.post(f"/api/webhooks/checkmk/{integration_id}", json=payload()).status_code == 401
    assert client.post(f"/api/webhooks/checkmk/{integration_id}", content=b"x" * 65537).status_code == 413


def test_rbac_and_audit(client, send, headers):
    incident_id = send(payload()).json()["incident_id"]
    viewer, analyst, admin = headers("viewer"), headers("analyst"), headers()
    path = f"/api/incidents/{incident_id}"
    assert client.get(path, headers=viewer).status_code == 200
    assert client.patch(path + "/status", json={"status": "RESOLVED"}, headers=viewer).status_code == 403
    assert client.post(path + "/comments", json={"body": "Test"}, headers=viewer).status_code == 403
    for auth in (viewer, analyst):
        assert client.get("/api/integrations", headers=auth).status_code == 403
        assert client.get("/api/audit", headers=auth).status_code == 403
        assert (
            client.post(
                "/api/users",
                json={
                    "email": "new@test.local",
                    "name": "New",
                    "role": "Admin",
                    "password": "new-password-strong",
                },
                headers=auth,
            ).status_code
            == 403
        )
    assert (
        client.post(path + "/comments", json={"body": "Investigação sintética"}, headers=analyst).status_code
        == 201
    )
    assert client.patch(path + "/status", json={"status": "ACKNOWLEDGED"}, headers=analyst).status_code == 200
    logs = client.get("/api/audit", headers=admin).json()["items"]
    assert {"event.ingested", "incident.created", "incident.commented", "incident.status_changed"} <= {
        a["action"] for a in logs
    }
    assert all(a["correlation_id"] for a in logs)
    assert client.get("/api/incidents/nonexistent", headers=viewer).status_code == 404


def test_assignment(client, send, headers):
    incident_id = send(payload()).json()["incident_id"]
    auth = headers("analyst")
    users = client.get("/api/users", headers=auth).json()
    viewer = next(u for u in users if u["role"] == "Viewer")
    analyst = next(u for u in users if u["role"] == "Analyst")
    path = f"/api/incidents/{incident_id}/assignment"
    assert client.patch(path, headers=auth, json={"assignee_id": viewer["id"]}).status_code == 422
    assert (
        client.patch(path, headers=auth, json={"assignee_id": analyst["id"]}).json()["assignee_id"]
        == analyst["id"]
    )


def test_dashboard_filters_and_inventory(client, send, headers):
    for event in scenario():
        assert send(event).status_code in {200, 201}
    auth = headers()
    summary = client.get("/api/dashboard", headers=auth)
    assert summary.status_code == 200, summary.text
    data = summary.json()
    assert data["open_incidents"] == 6 and data["events_24h"] == 6
    assert data["synthetic_events"] == 6 and data["mean_acknowledge_seconds"] is None
    assert data["critical_services"] == 2 and data["affected_hosts"] == 5
    assert sum(b["events"] for b in data["trend"]) == 6
    assert client.get("/api/incidents?severity=CRIT&limit=1", headers=auth).json()["total"] == 3
    assert client.get("/api/events?state=WARN", headers=auth).json()["total"] == 2
    assert client.get("/api/hosts", headers=auth).json()["total"] == 5
    assert client.get("/api/events?limit=201", headers=auth).status_code == 422


def test_secrets_never_listed_or_stored_plaintext(env, headers):
    client, factory, _ = env
    auth = headers()
    response = client.post("/api/integrations", json={"name": "Other lab"}, headers=auth)
    assert response.status_code == 201
    secret = response.json()["webhook_secret"]
    assert secret not in client.get("/api/integrations", headers=auth).text
    with factory() as db:
        assert secret not in db.get(Integration, response.json()["integration"]["id"]).webhook_secret
    assert "password" not in client.get("/api/auth/me", headers=auth).text


def test_redaction(client, send, headers):
    send({**payload(), "output": "password=confidential token:do-not-store normal diagnostic"})
    output = client.get("/api/events", headers=headers()).json()["items"][0]["output"]
    assert "confidential" not in output and "do-not-store" not in output and "[REDACTED]" in output


def test_concurrent_idempotency(env, send):
    _, factory, _ = env
    data = payload()
    with ThreadPoolExecutor(max_workers=4) as executor:
        responses = list(executor.map(lambda _: send(data), range(8)))
    assert [r.status_code for r in responses].count(201) == 1
    assert [r.status_code for r in responses].count(200) == 7
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(MonitoringEvent)) == 1
        assert db.scalar(select(func.count()).select_from(Incident)) == 1


def test_health_metrics_cors(client, headers):
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/ready").status_code == 200
    assert client.get("/metrics").status_code == 401
    assert "sentinel_http_requests_total" in client.get("/metrics", headers=headers()).text
    response = client.options(
        "/api/auth/login",
        headers={"Origin": "https://untrusted.invalid", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in response.headers
    assert client.get("/health").headers.get("x-correlation-id")


def test_login_rate_limit(client):
    statuses = [
        client.post("/api/auth/login", json={"email": "unknown@test.local", "password": "bad"}).status_code
        for _ in range(11)
    ]
    assert statuses[:10] == [401] * 10 and statuses[10] == 429


def test_openapi_documents_authenticated_raw_webhook(client):
    schema = client.get("/openapi.json").json()
    webhook = schema["paths"]["/api/webhooks/checkmk/{integration_id}"]["post"]
    assert webhook["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/EventIn")
    assert "external_id" in schema["components"]["schemas"]["EventIn"]["properties"]
    assert "RECOVERY" in schema["components"]["schemas"]["Severity"]["enum"]


def test_concurrent_different_events_share_one_incident(env, send):
    _, factory, _ = env
    with ThreadPoolExecutor(max_workers=4) as executor:
        responses = list(executor.map(lambda i: send(payload(number=i)), range(8)))
    assert all(r.status_code == 201 for r in responses)
    assert len({r.json()["incident_id"] for r in responses}) == 1
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(MonitoringEvent)) == 8
        assert db.scalar(select(func.count()).select_from(Incident)) == 1


def test_concurrent_source_id_reuse_on_different_resources(send):
    data = payload()
    variants = [data, {**data, "host": "other-host"}]
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(send, variants))
    assert sorted(r.status_code for r in responses) == [201, 409]


def test_manual_reopen_cannot_duplicate_active_scope(client, env, send, headers):
    _, factory, _ = env
    first = send(payload()).json()["incident_id"]
    send(payload("OK", 1))
    with factory() as db:
        db.get(Incident, first).resolved_at = utcnow() - timedelta(hours=1)
        db.commit()
    second = send(payload("CRIT", 2)).json()["incident_id"]
    assert first != second
    response = client.patch(f"/api/incidents/{first}/status", headers=headers(), json={"status": "OPEN"})
    assert response.status_code == 409


def test_flapping_expires_on_next_event(client, send, headers):
    for index, state in enumerate(["CRIT", "OK", "CRIT", "OK", "CRIT"]):
        data = payload(state, index)
        data["observed_at"] = (utcnow() - timedelta(seconds=1200 - index)).isoformat()
        first = send(data).json()["incident_id"]
    auth = headers()
    assert client.get(f"/api/incidents/{first}", headers=auth).json()["flapping"] is True
    send(payload(number=10))
    assert client.get(f"/api/incidents/{first}", headers=auth).json()["flapping"] is False


def test_rotated_webhook_secret_invalidates_old_secret(client, env, send, headers):
    _, _, integration = env
    result = client.post(f"/api/integrations/{integration}/rotate-secret", headers=headers())
    assert result.status_code == 200
    assert send(payload()).status_code == 401
    assert send(payload(), secret=result.json()["webhook_secret"]).status_code == 201


def test_invalid_payload_does_not_reflect_sensitive_input(client):
    response = client.post(
        "/api/auth/login", json={"email": "admin@test.local", "password": 123, "token": "secret-value"}
    )
    assert response.status_code == 422 and "secret-value" not in response.text


def test_retention_preserves_active_history(env, send, monkeypatch):
    _, factory, _ = env
    from app import cli
    from app.infrastructure.models import AuditLog

    active = send(payload(host="active-host")).json()
    old = send(payload(number=1, host="resolved-host")).json()
    send(payload("RECOVERY", number=2, host="resolved-host"))
    with factory() as db:
        for record in db.scalars(select(MonitoringEvent)):
            record.created_at = utcnow() - timedelta(days=100)
        db.add(
            AuditLog(action="test.expired", correlation_id="test", created_at=utcnow() - timedelta(days=400))
        )
        db.commit()
    monkeypatch.setattr(cli, "SessionLocal", factory)
    monkeypatch.setattr("sys.argv", ["cli", "retention"])
    cli.main()
    with factory() as db:
        assert db.get(MonitoringEvent, active["event_id"]) is not None
        assert db.get(MonitoringEvent, old["event_id"]) is None
        assert db.get(Incident, old["incident_id"]) is not None
        assert db.scalar(select(AuditLog).where(AuditLog.action == "test.expired")) is None
        assert db.scalar(select(AuditLog).where(AuditLog.action == "retention.executed")) is not None


def test_dashboard_keeps_first_partial_hour_in_rolling_window(env, send, headers):
    client, factory, _ = env
    event_id = send(payload()).json()["event_id"]
    with factory() as db:
        db.get(MonitoringEvent, event_id).created_at = utcnow() - timedelta(hours=23, minutes=59)
        db.commit()
    summary = client.get("/api/dashboard", headers=headers()).json()
    assert summary["events_24h"] == 1
    assert sum(b["events"] for b in summary["trend"]) == 1
