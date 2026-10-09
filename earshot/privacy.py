"""Privacy proof (01 §3.10). Real, measured, no guesses.

- bytes to the internet = localclient.internet_sent (0 by construction — the only
  HTTP client refuses non-local hosts before any socket opens).
- internet connections = sampled from psutil for OUR process (+ children) and the
  Ollama process(es): count remote endpoints that are NOT private/loopback.
Per-connection byte accounting isn't available on Windows, so we report the
localclient byte counters (exact for our traffic) + the live connection count.
"""

from __future__ import annotations

import ipaddress
import os
import time

import psutil

from . import localclient


def _is_public(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (addr.is_loopback or addr.is_private or addr.is_link_local or addr.is_unspecified)


def our_pids() -> set[int]:
    pids = {os.getpid()}
    try:
        for child in psutil.Process(os.getpid()).children(recursive=True):
            pids.add(child.pid)
    except Exception:
        pass
    return pids


def ollama_pids() -> set[int]:
    pids: set[int] = set()
    for p in psutil.process_iter(["name"]):
        try:
            if (p.info.get("name") or "").lower().startswith("ollama"):
                pids.add(p.pid)
        except Exception:
            continue
    return pids


def internet_connections(pids: set[int]) -> list[str]:
    """Remote public endpoints currently open by the given PIDs (should be empty)."""
    hits: list[str] = []
    try:
        conns = psutil.net_connections(kind="inet")
    except Exception:
        return hits  # may need elevation for other processes; report what we can
    for c in conns:
        if c.pid in pids and c.raddr:
            ip = c.raddr[0] if isinstance(c.raddr, tuple) else c.raddr.ip
            if _is_public(ip):
                hits.append(f"{ip}:{c.raddr[1] if isinstance(c.raddr, tuple) else c.raddr.port}")
    return hits


def _connections_snapshot() -> list[str]:
    pids = our_pids() | ollama_pids()
    return internet_connections(pids)


_cache: tuple[float, list[str]] = (0.0, [])


def _cached_connections(ttl: float = 3.0) -> list[str]:
    """psutil enumeration is slow on Windows; cache it so a polled /health never
    stalls the event loop thread for seconds."""
    global _cache
    now = time.monotonic()
    ts, val = _cache
    if now - ts > ttl:
        val = _connections_snapshot()
        _cache = (now, val)
    return val


def rss_mb() -> dict:
    """Resident memory (MB) for our process(es) + Ollama. Must stay < 3 GB total."""
    ours = sum(_rss(pid) for pid in our_pids())
    oll = sum(_rss(pid) for pid in ollama_pids())
    return {"earshot_mb": round(ours), "ollama_mb": round(oll), "total_mb": round(ours + oll)}


def _rss(pid: int) -> float:
    try:
        return psutil.Process(pid).memory_info().rss / 1024 / 1024
    except Exception:
        return 0.0


def proof() -> dict:
    c = localclient.counters()
    pub = _cached_connections()
    return {
        "internet_bytes_sent": c.internet_sent,   # 0 by construction
        "internet_bytes_recv": c.internet_recv,
        "local_bytes_sent": c.local_sent,         # loopback (Ollama) — fine
        "local_bytes_recv": c.local_recv,
        "internet_connections": len(pub),
        "internet_endpoints": pub[:10],
        "requests": c.requests,
    }
