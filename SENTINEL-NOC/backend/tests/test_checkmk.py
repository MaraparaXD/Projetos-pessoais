from unittest.mock import patch

import pytest

from app.infrastructure.checkmk import CheckmkRestAdapter, CheckmkUnavailable, MockCheckmkRestAdapter
from app.interfaces.schemas import EventIn
from scripts.checkmk_notification import normalize


def test_notification_environment_normalization():
    data = normalize(
        {
            "NOTIFY_WHAT": "SERVICE",
            "NOTIFY_HOSTNAME": "lab-db-01",
            "NOTIFY_SERVICEDESC": "PostgreSQL",
            "NOTIFY_SERVICESTATE": "CRITICAL",
            "NOTIFY_SERVICEOUTPUT": "Synthetic",
            "NOTIFY_LASTSERVICESTATECHANGE": "1780000000",
        }
    )
    assert EventIn.model_validate(data).state == "CRIT"
    assert (
        normalize(
            {
                "NOTIFY_WHAT": "HOST",
                "NOTIFY_HOSTNAME": "lab-edge-01",
                "NOTIFY_HOSTSTATE": "UP",
                "NOTIFY_NOTIFICATIONTYPE": "RECOVERY",
                "NOTIFY_LASTHOSTSTATECHANGE": "1780000000",
            }
        )["state"]
        == "RECOVERY"
    )


def test_mock_is_explicit():
    assert all(h["extensions"]["synthetic"] for h in MockCheckmkRestAdapter().list_hosts())


@pytest.mark.parametrize(
    "url",
    [
        "http://public.example/site/check_mk/api/1.0",
        "https://other.example/site/check_mk/api/1.0",
        "https://user:pass@public.example/site/check_mk/api/1.0",
        "https://public.example:8443/site/check_mk/api/1.0",
    ],
)
def test_rest_rejects_invalid_destination(url):
    with pytest.raises(ValueError):
        CheckmkRestAdapter(url, "automation", "secret", {"public.example"})


def test_rest_rejects_private_dns():
    adapter = CheckmkRestAdapter(
        "https://public.example/site/check_mk/api/1.0", "automation", "secret", {"public.example"}
    )
    with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 443))]):
        with pytest.raises(CheckmkUnavailable):
            adapter.list_hosts()
