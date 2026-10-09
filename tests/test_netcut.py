"""The net-cut rule builder must reproduce 01 §3.11 exactly, and the shipped
scripts must contain those same rules (07: 'net-cut rule builder produces the
exact commands')."""

from pathlib import Path

from earshot import netcut

REPO_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_CUT = [
    '$v4 = "1.0.0.0-9.255.255.255","11.0.0.0-126.255.255.255","128.0.0.0-169.253.255.255","169.255.0.0-172.15.255.255","172.32.0.0-192.167.255.255","192.169.0.0-223.255.255.255"',
    'New-NetFirewallRule -Group "EarshotOffline" -DisplayName "Earshot offline: block internet IPv4" -Direction Outbound -Action Block -RemoteAddress $v4 -Profile Any',
    'New-NetFirewallRule -Group "EarshotOffline" -DisplayName "Earshot offline: block internet IPv6" -Direction Outbound -Action Block -RemoteAddress "2000::-3fff:ffff:ffff:ffff:ffff:ffff:ffff:ffff" -Profile Any',
    'New-NetFirewallRule -Group "EarshotOffline" -DisplayName "Earshot offline: block DNS via hotspot UDP" -Direction Outbound -Action Block -Protocol UDP -RemotePort 53 -RemoteAddress "172.20.10.1" -Profile Any',
    'New-NetFirewallRule -Group "EarshotOffline" -DisplayName "Earshot offline: block DNS via hotspot TCP" -Direction Outbound -Action Block -Protocol TCP -RemotePort 53 -RemoteAddress "172.20.10.1" -Profile Any',
]
EXPECTED_RESTORE = 'Remove-NetFirewallRule -Group "EarshotOffline"'


def test_cut_commands_exact():
    assert netcut.cut_commands() == EXPECTED_CUT


def test_restore_command_exact():
    assert netcut.restore_command() == EXPECTED_RESTORE


def test_group_matches_brand():
    assert netcut.group() == "EarshotOffline"


def test_scripts_contain_exact_rules():
    cut = (REPO_ROOT / "scripts" / "cut-internet.ps1").read_text(encoding="utf-8")
    for line in EXPECTED_CUT:
        assert line in cut, f"missing from cut-internet.ps1:\n{line}"
    restore = (REPO_ROOT / "scripts" / "restore-internet.ps1").read_text(encoding="utf-8")
    assert EXPECTED_RESTORE in restore


def test_private_ranges_not_blocked():
    """Hotspot LAN (172.16/12, incl. 172.20.10.x) and other private ranges must
    stay reachable, so the iPhone still loads the phone page."""
    joined = " ".join(netcut.V4_RANGES)
    # The 172.16-31 block is carved out of the ranges (169.255 -> 172.15, 172.32 -> ...).
    assert "172.16" not in joined
    assert "10.0.0.0" not in joined
    assert "192.168" not in joined
