"""Cut-internet toggle via Windows Firewall (01 §3.11).

Blocks every non-private IPv4 destination, all global IPv6, and DNS via the
hotspot gateway, while leaving the hotspot LAN (incl. 172.16/12) reachable so
the iPhone can still load the phone page. Block rules beat allow rules in
Windows Firewall.

The rule strings here reproduce 01 §3.11 verbatim for the default brand; the
group/display name read ``brand.display_name()`` so a rename stays consistent
between cut and restore. Needs an elevated (admin) PowerShell to take effect.

``earshot net cut|restore|status`` and the dashboard switch call this. Restore
is also wired to run on daemon exit so the laptop is never left cut off.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass

from . import brand

# Non-private IPv4 ranges to block (everything except 10/8, 127/8, 169.254/16,
# 172.16/12, 192.168/16). Verbatim from 01 §3.11.
V4_RANGES = [
    "1.0.0.0-9.255.255.255",
    "11.0.0.0-126.255.255.255",
    "128.0.0.0-169.253.255.255",
    "169.255.0.0-172.15.255.255",
    "172.32.0.0-192.167.255.255",
    "192.169.0.0-223.255.255.255",
]
IPV6_RANGE = "2000::-3fff:ffff:ffff:ffff:ffff:ffff:ffff:ffff"
HOTSPOT_GATEWAY = "172.20.10.1"


def group() -> str:
    """Firewall rule group, e.g. ``EarshotOffline``."""
    return f"{brand.display_name()}Offline"


def _display(suffix: str) -> str:
    return f"{brand.display_name()} offline: {suffix}"


def _v4_literal() -> str:
    return ",".join(f'"{r}"' for r in V4_RANGES)


def cut_commands() -> list[str]:
    """The exact PowerShell statements that create the block rules (01 §3.11)."""
    g = group()
    return [
        f"$v4 = {_v4_literal()}",
        (
            f'New-NetFirewallRule -Group "{g}" -DisplayName "{_display("block internet IPv4")}" '
            f"-Direction Outbound -Action Block -RemoteAddress $v4 -Profile Any"
        ),
        (
            f'New-NetFirewallRule -Group "{g}" -DisplayName "{_display("block internet IPv6")}" '
            f'-Direction Outbound -Action Block -RemoteAddress "{IPV6_RANGE}" -Profile Any'
        ),
        (
            f'New-NetFirewallRule -Group "{g}" -DisplayName "{_display("block DNS via hotspot UDP")}" '
            f'-Direction Outbound -Action Block -Protocol UDP -RemotePort 53 -RemoteAddress "{HOTSPOT_GATEWAY}" -Profile Any'
        ),
        (
            f'New-NetFirewallRule -Group "{g}" -DisplayName "{_display("block DNS via hotspot TCP")}" '
            f'-Direction Outbound -Action Block -Protocol TCP -RemotePort 53 -RemoteAddress "{HOTSPOT_GATEWAY}" -Profile Any'
        ),
    ]


def restore_command() -> str:
    """The exact PowerShell statement that removes the block rules (01 §3.11)."""
    return f'Remove-NetFirewallRule -Group "{group()}"'


def status_command() -> str:
    return (
        f'Get-NetFirewallRule -Group "{group()}" -ErrorAction SilentlyContinue | '
        f"Select-Object DisplayName, Enabled, Action, Direction"
    )


# ---- runtime helpers (call PowerShell; need admin for cut/restore to apply) ----


@dataclass
class NetResult:
    ok: bool
    output: str
    error: str = ""


def _run_ps(script: str, timeout: float = 20.0) -> NetResult:
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:  # pragma: no cover - env dependent
        return NetResult(ok=False, output="", error=str(exc))
    return NetResult(ok=proc.returncode == 0, output=proc.stdout.strip(), error=proc.stderr.strip())


def is_elevated() -> bool:
    """True iff the current process runs as Administrator."""
    try:  # pragma: no cover - Windows only
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def cut() -> NetResult:
    script = "\n".join(cut_commands())
    return _run_ps(script)


def restore() -> NetResult:
    # -ErrorAction SilentlyContinue so calling restore when nothing is set is a no-op.
    return _run_ps(f"{restore_command()} -ErrorAction SilentlyContinue")


def status() -> NetResult:
    return _run_ps(status_command())


def is_cut() -> bool:
    res = status()
    return res.ok and bool(res.output)


_cut_cache: tuple[float, bool] = (0.0, False)


def is_cut_cached(ttl: float = 5.0) -> bool:
    """is_cut() with a short TTL so a polled /health endpoint doesn't spawn a
    PowerShell process on every request."""
    global _cut_cache
    now = time.monotonic()
    ts, val = _cut_cache
    if now - ts > ttl:
        val = is_cut()
        _cut_cache = (now, val)
    return val
