"""Consulta o inventário Checkmk sem alterar o ambiente."""

import http.client
import ipaddress
import json
import socket
import ssl
from urllib.parse import urlsplit


class CheckmkUnavailable(RuntimeError):
    pass


class _PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, port, address):
        super().__init__(host, port=port, timeout=10, context=ssl.create_default_context())
        self.address = address

    def connect(self):

        sock = socket.create_connection((self.address, self.port), timeout=self.timeout)
        try:
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except Exception:
            sock.close()
            raise


class CheckmkRestAdapter:
    def __init__(self, api_url: str, username: str, automation_secret: str, allowed_hosts: set[str]):
        url = urlsplit(api_url)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.hostname not in allowed_hosts
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.port not in {None, 443}
            or not url.path.rstrip("/").endswith(("/check_mk/api/1.0", "/check_mk/api/v1"))
        ):
            raise ValueError("Use an allowlisted HTTPS Checkmk API URL on port 443")
        if any(c in username + automation_secret for c in "\r\n"):
            raise ValueError("Invalid credentials")
        self.url, self.username, self.secret = url, username, automation_secret

    def list_hosts(self) -> list[dict]:
        try:
            addresses = socket.getaddrinfo(self.url.hostname, 443, type=socket.SOCK_STREAM)
            if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
                raise ValueError("Private, loopback and reserved destinations are prohibited")
            connection = _PinnedHTTPS(self.url.hostname, 443, addresses[0][4][0])
            try:
                connection.request(
                    "GET",
                    self.url.path.rstrip("/") + "/domain-types/host_config/collections/all",
                    headers={
                        "Authorization": f"Bearer {self.username} {self.secret}",
                        "Accept": "application/json",
                    },
                )
                response = connection.getresponse()
                if response.status != 200:
                    raise CheckmkUnavailable(f"Checkmk returned HTTP {response.status}; no redirect followed")
                body = response.read(2 * 1024 * 1024 + 1)
                if len(body) > 2 * 1024 * 1024:
                    raise CheckmkUnavailable("Checkmk response exceeds 2 MiB")
                payload = json.loads(body)
                if not isinstance(payload, dict) or not isinstance(payload.get("value"), list):
                    raise CheckmkUnavailable("Unsupported Checkmk inventory response")
                return payload["value"]
            finally:
                connection.close()
        except (OSError, ValueError) as exc:
            raise CheckmkUnavailable("Checkmk unavailable or destination rejected") from exc


class MockCheckmkRestAdapter:
    """Fornece inventário sintético para testes locais."""

    def list_hosts(self):
        return [
            {"id": "lab-edge-01", "title": "lab-edge-01", "extensions": {"synthetic": True}},
            {"id": "lab-db-01", "title": "lab-db-01", "extensions": {"synthetic": True}},
        ]
