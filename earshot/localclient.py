"""The ONLY HTTP client in the app (CLAUDE.md non-negotiable).

- Refuses any host that is not loopback or RFC-1918/link-local private.
- Counts bytes sent/received so the privacy panel shows real numbers.
- Used only to talk to Ollama (127.0.0.1:11434) and never anything else.

If a public host is ever requested, we raise ``PublicHostRefused`` *before* any
socket is opened, so "bytes sent to the internet" is 0 by construction.
"""

from __future__ import annotations

import ipaddress
import socket
import threading
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx


class PublicHostRefused(RuntimeError):
    """Raised when a non-local/non-private host is requested."""


@dataclass
class Counters:
    # internet_* = bytes to NON-private destinations (0 by construction: we refuse
    # public hosts before any socket opens). local_* = loopback/private (Ollama).
    internet_sent: int = 0
    internet_recv: int = 0
    local_sent: int = 0
    local_recv: int = 0
    requests: int = 0

    # Back-compat alias: the privacy panel's "bytes to the internet".
    @property
    def bytes_sent(self) -> int:
        return self.internet_sent

    @property
    def bytes_recv(self) -> int:
        return self.internet_recv


_counters = Counters()
_lock = threading.Lock()


def counters() -> Counters:
    with _lock:
        return Counters(
            _counters.internet_sent, _counters.internet_recv,
            _counters.local_sent, _counters.local_recv, _counters.requests,
        )


def reset_counters() -> None:
    with _lock:
        _counters.internet_sent = _counters.internet_recv = 0
        _counters.local_sent = _counters.local_recv = 0
        _counters.requests = 0


def _is_private_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return (
        addr.is_loopback
        or addr.is_private
        or addr.is_link_local
        or addr.is_unspecified
    )


def is_local_host(host: str) -> bool:
    """True iff *host* resolves only to loopback/private addresses.

    A bare hostname is resolved; if ANY resolved address is public, it is
    refused. ``localhost`` and literal private IPs pass.
    """
    if not host:
        return False
    # Literal IP?
    try:
        ipaddress.ip_address(host)
        return _is_private_ip(host)
    except ValueError:
        pass
    # Hostname: resolve and require every address to be private.
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    addrs = {info[4][0] for info in infos}
    return bool(addrs) and all(_is_private_ip(a) for a in addrs)


def _guard(url: str) -> None:
    host = urlparse(url).hostname or ""
    if not is_local_host(host):
        raise PublicHostRefused(
            f"localclient refuses non-local host {host!r}: all inference stays on this laptop."
        )


def _count(payload: bytes | None, response: httpx.Response, host: str) -> None:
    # Every request here has already passed _guard (host is loopback/private), so
    # it counts as LOCAL. internet_* only moves if a public host ever slipped
    # through (it can't) — which is exactly the guarantee the panel shows.
    is_local = is_local_host(host)
    with _lock:
        _counters.requests += 1
        sent = len(payload) if payload is not None else 0
        recv = len(response.content)
        if is_local:
            _counters.local_sent += sent
            _counters.local_recv += recv
        else:
            _counters.internet_sent += sent
            _counters.internet_recv += recv


def post_json(url: str, json_body: dict, timeout: float = 12.0) -> httpx.Response:
    """POST JSON to a guaranteed-local URL, counting bytes. Guards first."""
    _guard(url)
    import json as _json

    payload = _json.dumps(json_body).encode("utf-8")
    host = urlparse(url).hostname or ""
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, content=payload, headers={"content-type": "application/json"})
    _count(payload, resp, host)
    return resp


def get(url: str, timeout: float = 5.0) -> httpx.Response:
    """GET a guaranteed-local URL, counting bytes. Guards first."""
    _guard(url)
    host = urlparse(url).hostname or ""
    with httpx.Client(timeout=timeout) as client:
        resp = client.get(url)
    _count(None, resp, host)
    return resp
