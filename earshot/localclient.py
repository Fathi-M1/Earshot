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
    bytes_sent: int = 0
    bytes_recv: int = 0
    requests: int = 0


_counters = Counters()
_lock = threading.Lock()


def counters() -> Counters:
    with _lock:
        return Counters(_counters.bytes_sent, _counters.bytes_recv, _counters.requests)


def reset_counters() -> None:
    with _lock:
        _counters.bytes_sent = 0
        _counters.bytes_recv = 0
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


def _count(payload: bytes | None, response: httpx.Response) -> None:
    with _lock:
        _counters.requests += 1
        if payload is not None:
            _counters.bytes_sent += len(payload)
        _counters.bytes_recv += len(response.content)


def post_json(url: str, json_body: dict, timeout: float = 12.0) -> httpx.Response:
    """POST JSON to a guaranteed-local URL, counting bytes. Guards first."""
    _guard(url)
    import json as _json

    payload = _json.dumps(json_body).encode("utf-8")
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, content=payload, headers={"content-type": "application/json"})
    _count(payload, resp)
    return resp


def get(url: str, timeout: float = 5.0) -> httpx.Response:
    """GET a guaranteed-local URL, counting bytes. Guards first."""
    _guard(url)
    with httpx.Client(timeout=timeout) as client:
        resp = client.get(url)
    _count(None, resp)
    return resp
