from __future__ import annotations

import argparse
import ipaddress
import json
import mimetypes
import os
import re
import sys
import threading
import time
from collections import defaultdict, deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .errors import (
    DuplicateSubmission,
    InvalidTransition,
    NotFound,
    QueueFull,
    FieldLabError,
    Unauthorized,
    ValidationError,
)
from .github import GitHubVerifier
from .service import WorkService

STATIC_DIR = Path(__file__).with_name("static")
WORK_RE = re.compile(r"^/api/work/(?P<ref>OWP-[A-F0-9]{8,64})$")
ANSWER_RE = re.compile(r"^/api/work/(?P<ref>OWP-[A-F0-9]{8,64})/answer$")
DISPOSITION_RE = re.compile(r"^/api/work/(?P<ref>OWP-[A-F0-9]{8,64})/disposition$")
HANDOFF_RE = re.compile(r"^/api/work/(?P<ref>OWP-[A-F0-9]{8,64})/handoff$")


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = max(1, int(limit))
        self.window_seconds = max(1, int(window_seconds))
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def acquire(self, key: str) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                retry = max(1, int(self.window_seconds - (now - events[0])))
                return False, retry
            events.append(now)
            return True, 0


class OWPFieldLabHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address,
        handler,
        service: WorkService,
        sse_interval: float = 10.0,
        sse_max_clients: int = 32,
        submission_limit: int = 5,
        submission_window_seconds: int = 3600,
        trust_proxy: bool = False,
    ):
        super().__init__(server_address, handler)
        self.service = service
        self.sse_interval = sse_interval
        self.closing = threading.Event()
        self.sse_slots = threading.BoundedSemaphore(max(1, int(sse_max_clients)))
        self.submission_limiter = SlidingWindowLimiter(submission_limit, submission_window_seconds)
        self.trust_proxy = bool(trust_proxy)

    def server_close(self):
        self.closing.set()
        return super().server_close()


class Handler(BaseHTTPRequestHandler):
    server_version = "OWPFieldLab/0.1"
    sys_version = ""

    @property
    def svc(self) -> WorkService:
        return self.server.service  # type: ignore[attr-defined]

    def log_message(self, fmt, *args):
        sys.stderr.write(
            "%s - - [%s] %s\n"
            % (self.client_address[0], self.log_date_time_string(), fmt % args)
        )

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; connect-src 'self'; style-src 'self'; script-src 'self'; "
            "img-src 'self' data:; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
        )

    def _json(self, status: int, body: dict, extra_headers: dict[str, str] | None = None):
        raw = json.dumps(body, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self._security_headers()
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> dict:
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise ValidationError("Content-Type must be application/json.")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValidationError("Invalid Content-Length.")
        if length < 1 or length > 16_384:
            raise ValidationError("JSON body must be between 1 and 16,384 bytes.")
        raw = self.rfile.read(length)
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError("Request body must be valid JSON.") from exc
        if not isinstance(value, dict):
            raise ValidationError("JSON body must be an object.")
        return value

    def _bearer(self) -> str:
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise Unauthorized("Missing claim token.")
        token = auth[7:].strip()
        if not token:
            raise Unauthorized("Missing claim token.")
        return token

    def _client_key(self) -> str:
        raw = self.client_address[0]
        if self.server.trust_proxy:  # type: ignore[attr-defined]
            forwarded = self.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
            if forwarded:
                try:
                    ipaddress.ip_address(forwarded)
                    raw = forwarded
                except ValueError:
                    pass
        try:
            return ipaddress.ip_address(raw).compressed
        except ValueError:
            return raw[:128]

    def _handle_error(self, exc: Exception):
        if isinstance(exc, (QueueFull, DuplicateSubmission)):
            status = HTTPStatus.CONFLICT
        elif isinstance(exc, (Unauthorized, NotFound)):
            # Do not expose whether a guessed work reference exists.
            status = HTTPStatus.NOT_FOUND
        elif isinstance(exc, (ValidationError, InvalidTransition)):
            status = HTTPStatus.BAD_REQUEST
        elif isinstance(exc, FieldLabError):
            status = HTTPStatus.BAD_REQUEST
        else:
            self.log_error("internal error: %r", exc)
            status = HTTPStatus.INTERNAL_SERVER_ERROR
        message = (
            "Not found."
            if isinstance(exc, (Unauthorized, NotFound))
            else str(exc)
            if status != HTTPStatus.INTERNAL_SERVER_ERROR
            else "Internal server error."
        )
        self._json(status, {"error": message})

    def do_GET(self):
        try:
            path = urlparse(self.path).path
            if path == "/healthz":
                result = self.svc.verify_all()
                status = 200 if result["ok"] else 503
                return self._json(
                    status,
                    {
                        "ok": result["ok"],
                        "sqlite": result["sqlite_quick_check"],
                        "work_items_checked": result["work_items_checked"],
                    },
                )
            if path == "/api/status":
                return self._json(200, self.svc.public_status())
            if path == "/api/owp/describe":
                return self._json(200, {
                    "profile": "owp-field-lab/0.1",
                    "status": "field-lab",
                    "conformance_claim": False,
                    "work_types": ["github_pr", "idea"],
                    "lifecycle": ["proposed", "todo", "in_progress", "parked", "review", "completed", "cancelled"],
                    "customer_actions": ["answer", "approve", "steer", "reject", "export_handoff"],
                    "provider_actions": ["accept", "pass", "start", "ask", "deliver", "validate"],
                    "queue_max": self.svc.queue_max,
                })
            if path == "/api/live":
                return self._sse()
            match = WORK_RE.fullmatch(path)
            if match:
                return self._json(200, self.svc.get_work(match.group("ref"), self._bearer()))
            match = HANDOFF_RE.fullmatch(path)
            if match:
                return self._json(200, self.svc.customer_handoff(match.group("ref"), self._bearer()))
            if path.startswith("/admin") or path.startswith("/api/admin"):
                return self._json(404, {"error": "Not found."})
            return self._static(path)
        except Exception as exc:
            self._handle_error(exc)

    def do_POST(self):
        try:
            path = urlparse(self.path).path
            if path == "/api/submissions":
                allowed, retry_after = self.server.submission_limiter.acquire(  # type: ignore[attr-defined]
                    self._client_key()
                )
                if not allowed:
                    return self._json(
                        HTTPStatus.TOO_MANY_REQUESTS,
                        {"error": "Too many submission attempts from this client. Try again later."},
                        {"Retry-After": str(retry_after)},
                    )
                body = self._read_json()
                result = self.svc.submit(
                    body.get("work_kind", "github_pr"),
                    body.get("value_usd", body.get("bid_usd", "")),
                    body.get("outcome", ""),
                    attested=body.get("attested") is True,
                    pr_url=body.get("pr_url", ""),
                    idea_title=body.get("idea_title", ""),
                    context_url=body.get("context_url", ""),
                )
                return self._json(201, result)
            match = ANSWER_RE.fullmatch(path)
            if match:
                body = self._read_json()
                result = self.svc.answer(
                    match.group("ref"),
                    self._bearer(),
                    body.get("question_id", ""),
                    body.get("option", ""),
                    body.get("note", ""),
                )
                return self._json(200, result)
            match = DISPOSITION_RE.fullmatch(path)
            if match:
                body = self._read_json()
                result = self.svc.disposition(
                    match.group("ref"),
                    self._bearer(),
                    body.get("action", ""),
                    body.get("note", ""),
                )
                return self._json(200, result)
            if path.startswith("/admin") or path.startswith("/api/admin"):
                return self._json(404, {"error": "Not found."})
            return self._json(404, {"error": "Not found."})
        except Exception as exc:
            self._handle_error(exc)

    def _sse(self):
        slots = self.server.sse_slots  # type: ignore[attr-defined]
        if not slots.acquire(blocking=False):
            return self._json(503, {"error": "Live capacity stream is busy; retry shortly."})
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")
            self._security_headers()
            self.end_headers()
            last = None
            for _ in range(180):
                if self.server.closing.is_set():  # type: ignore[attr-defined]
                    return
                try:
                    current = self.svc.public_status()
                except Exception as exc:
                    self.log_error("capacity stream stopped: %r", exc)
                    return
                encoded = json.dumps(current, separators=(",", ":"))
                try:
                    if encoded != last:
                        self.wfile.write(f"event: capacity\ndata: {encoded}\n\n".encode("utf-8"))
                        self.wfile.flush()
                        last = encoded
                    else:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    return
                time.sleep(self.server.sse_interval)  # type: ignore[attr-defined]
        finally:
            slots.release()

    def _static(self, path: str):
        mapping = {
            "": "index.html",
            "/": "index.html",
            "/privacy": "privacy.html",
            "/privacy.html": "privacy.html",
            "/app.js": "app.js",
            "/styles.css": "styles.css",
        }
        filename = mapping.get(path)
        if not filename:
            return self._json(404, {"error": "Not found."})
        target = STATIC_DIR / filename
        raw = target.read_bytes()
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header(
            "Content-Type",
            ctype
            + (
                "; charset=utf-8"
                if ctype.startswith("text/") or ctype == "application/javascript"
                else ""
            ),
        )
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(raw)))
        self._security_headers()
        self.end_headers()
        self.wfile.write(raw)


def create_server(
    service: WorkService,
    host: str = "127.0.0.1",
    port: int = 8080,
    sse_interval: float = 10.0,
    sse_max_clients: int = 32,
    submission_limit: int = 5,
    submission_window_seconds: int = 3600,
    trust_proxy: bool = False,
) -> OWPFieldLabHTTPServer:
    return OWPFieldLabHTTPServer(
        (host, port),
        Handler,
        service,
        sse_interval=sse_interval,
        sse_max_clients=sse_max_clients,
        submission_limit=submission_limit,
        submission_window_seconds=submission_window_seconds,
        trust_proxy=trust_proxy,
    )


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the OWP public field lab")
    parser.add_argument("--host", default=os.environ.get("OWP_FIELD_LAB_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("OWP_FIELD_LAB_PORT", "8080")))
    parser.add_argument("--db", default=os.environ.get("OWP_FIELD_LAB_DB", "./data/owp-field-lab.sqlite3"))
    parser.add_argument(
        "--queue-max", type=int, default=int(os.environ.get("OWP_FIELD_LAB_QUEUE_MAX", "20"))
    )
    args = parser.parse_args(argv)

    verifier = GitHubVerifier(token=os.environ.get("GITHUB_TOKEN"))
    service = WorkService(args.db, queue_max=args.queue_max, verifier=verifier, provider_actor=os.environ.get("OWP_FIELD_LAB_PROVIDER_ID", "provider"))
    server = create_server(
        service,
        args.host,
        args.port,
        sse_interval=float(os.environ.get("OWP_FIELD_LAB_SSE_INTERVAL", "10")),
        sse_max_clients=int(os.environ.get("OWP_FIELD_LAB_SSE_MAX_CLIENTS", "32")),
        submission_limit=int(os.environ.get("OWP_FIELD_LAB_SUBMISSIONS_PER_HOUR", "5")),
        submission_window_seconds=3600,
        trust_proxy=env_bool("OWP_FIELD_LAB_TRUST_PROXY"),
    )
    print(f"OWP Field Lab listening on http://{args.host}:{args.port} (queue max {args.queue_max})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
