import json
import logging
import time
import uuid

from prometheus_client import Counter, Histogram
from redis.exceptions import RedisError
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse

from app.application.audit import correlation_id
from app.core.config import get_settings
from app.infrastructure.limiter import RateLimiter

REQUESTS = Counter("sentinel_http_requests_total", "Requests", ["method", "route", "status"])
DURATION = Histogram("sentinel_http_request_duration_seconds", "Latency", ["method", "route"])
logger = logging.getLogger("sentinel.http")


class SafetyMiddleware:
    def __init__(self, app):
        self.app = app
        self.settings = get_settings()
        self.limiter = RateLimiter(self.settings.redis_url)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = str(uuid.uuid4())
        context = correlation_id.set(request_id)
        started, status = time.perf_counter(), 500

        async def wrapped_send(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message["headers"] += [
                    (b"x-correlation-id", request_id.encode()),
                    (b"x-content-type-options", b"nosniff"),
                    (b"cache-control", b"no-store"),
                    (b"referrer-policy", b"no-referrer"),
                ]
            await send(message)

        async def reject(code, detail, headers=None):
            await JSONResponse({"detail": detail}, status_code=code, headers=headers)(
                scope, receive, wrapped_send
            )

        try:
            path = scope["path"]
            if path.startswith("/api/"):
                is_login = path == "/api/auth/login"
                key = f"{scope.get('client', ('unknown',))[0]}:{'login' if is_login else 'api'}"
                limit = (
                    self.settings.login_rate_limit_per_minute
                    if is_login
                    else self.settings.rate_limit_per_minute
                )
                try:
                    allowed = await run_in_threadpool(self.limiter.allow, key, limit)
                except RedisError:
                    return await reject(503, "Rate limiter unavailable")
                if not allowed:
                    return await reject(429, "Too many requests; retry in one minute", {"Retry-After": "60"})
            if scope["method"] in {"POST", "PUT", "PATCH"}:
                headers = dict(scope["headers"])
                try:
                    if int(headers.get(b"content-length", b"0")) > self.settings.max_body_bytes:
                        return await reject(413, "Payload exceeds 64 KiB")
                except ValueError:
                    return await reject(400, "Invalid content length")
                body = bytearray()
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    body.extend(message.get("body", b""))
                    if len(body) > self.settings.max_body_bytes:
                        return await reject(413, "Payload exceeds 64 KiB")
                    if not message.get("more_body", False):
                        break
                delivered = False

                async def bounded_receive():
                    nonlocal delivered
                    if not delivered:
                        delivered = True
                        return {"type": "http.request", "body": bytes(body), "more_body": False}
                    return await receive()

                await self.app(scope, bounded_receive, wrapped_send)
            else:
                await self.app(scope, receive, wrapped_send)
        finally:
            route = getattr(scope.get("route"), "path", "unmatched")
            elapsed = time.perf_counter() - started
            REQUESTS.labels(scope["method"], route, str(status)).inc()
            DURATION.labels(scope["method"], route).observe(elapsed)
            logger.info(
                json.dumps(
                    {
                        "correlation_id": request_id,
                        "method": scope["method"],
                        "route": route,
                        "status": status,
                        "duration_ms": round(elapsed * 1000, 2),
                    }
                )
            )
            correlation_id.reset(context)
