"""HTTP Basic authentication support for the AKS Store Demo MCP servers.

Both MCP servers are exposed over the streamable HTTP transport, which means
they are reachable as plain network services. This module adds a small ASGI
middleware that requires HTTP Basic credentials on every request except the
health endpoints.

Credentials are read from the environment:

    MCP_AUTH_USERNAME   username clients must present
    MCP_AUTH_PASSWORD   password clients must present
    MCP_AUTH_ENABLED    set to "false" to disable auth (local development only)

Authentication is enabled by default, so the server refuses to start when the
credentials are missing. That keeps the deployment secure by default instead of
silently exposing the tools to anonymous callers.
"""

import base64
import binascii
import hmac
import os
from typing import Iterable, Sequence

import uvicorn

# Paths that stay open so container/Kubernetes probes and load balancers keep
# working without credentials.
DEFAULT_PUBLIC_PATHS: Sequence[str] = ("/health", "/healthz", "/readyz")


_TRUE_VALUES = ("1", "true", "yes", "on")
_FALSE_VALUES = ("0", "false", "no", "off")


def auth_enabled() -> bool:
    """Return True when Basic authentication should be enforced.

    Only recognized true/false values are accepted; anything else (including a
    typo such as "flase") is rejected so the server fails closed instead of
    silently running without authentication.
    """
    raw = os.getenv("MCP_AUTH_ENABLED", "true").strip().lower()
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    raise RuntimeError(
        f"Invalid MCP_AUTH_ENABLED value {raw!r}. Use one of {_TRUE_VALUES + _FALSE_VALUES}."
    )


class BasicAuthMiddleware:
    """Pure ASGI middleware enforcing HTTP Basic authentication.

    A pure ASGI implementation is used (instead of Starlette's
    ``BaseHTTPMiddleware``) so that the streaming responses used by the MCP
    streamable HTTP transport are passed through untouched.
    """

    def __init__(
        self,
        app,
        username: str,
        password: str,
        realm: str = "MCP Server",
        public_paths: Iterable[str] = DEFAULT_PUBLIC_PATHS,
    ) -> None:
        if not username or not password:
            raise ValueError("Basic auth requires a non-empty username and password")
        self.app = app
        self._username = username
        self._password = password
        self._realm = realm
        self._public_paths = tuple(public_paths)

    def _is_public(self, path: str) -> bool:
        return any(path == public or path.startswith(public + "/") for public in self._public_paths)

    def _credentials_valid(self, header_value: str) -> bool:
        scheme, _, encoded = header_value.partition(" ")
        if scheme.lower() != "basic" or not encoded:
            return False
        try:
            decoded = base64.b64decode(encoded.strip(), validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            return False
        username, separator, password = decoded.partition(":")
        if not separator:
            return False
        # Compare both values (without short-circuiting) to avoid leaking which
        # half of the credentials was wrong through response timing.
        username_ok = hmac.compare_digest(username, self._username)
        password_ok = hmac.compare_digest(password, self._password)
        return username_ok and password_ok

    async def _unauthorized(self, send) -> None:
        body = b'{"error":"Unauthorized"}'
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"www-authenticate", f'Basic realm="{self._realm}"'.encode("utf-8")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if self._is_public(scope.get("path", "")):
            await self.app(scope, receive, send)
            return

        headers = {key.decode("latin-1").lower(): value.decode("latin-1") for key, value in scope.get("headers", [])}
        authorization = headers.get("authorization", "")
        if not authorization or not self._credentials_valid(authorization):
            await self._unauthorized(send)
            return

        await self.app(scope, receive, send)


def build_app(mcp, realm: str):
    """Return the streamable HTTP ASGI app, wrapped with Basic auth if enabled."""
    app = mcp.streamable_http_app()

    if not auth_enabled():
        print(
            "WARNING: MCP_AUTH_ENABLED is false - the MCP server is running "
            "without authentication. Use this only for local development.",
            flush=True,
        )
        return app

    username = os.getenv("MCP_AUTH_USERNAME", "")
    password = os.getenv("MCP_AUTH_PASSWORD", "")
    if not username or not password:
        raise RuntimeError(
            "MCP_AUTH_USERNAME and MCP_AUTH_PASSWORD must be set to enable HTTP "
            "Basic authentication. Set MCP_AUTH_ENABLED=false to run without "
            "authentication (local development only)."
        )

    return BasicAuthMiddleware(app, username=username, password=password, realm=realm)


def run(mcp, realm: str) -> None:
    """Serve the MCP server over streamable HTTP with Basic authentication."""
    uvicorn.run(
        build_app(mcp, realm),
        host=mcp.settings.host,
        port=mcp.settings.port,
        log_level=mcp.settings.log_level.lower(),
    )
