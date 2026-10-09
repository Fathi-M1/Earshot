"""Earshot CLI: serve · bench · net cut|restore|status · doctor · wipe.

Name/help text reads brand.display_name() (never hard-coded).
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
from pathlib import Path

from . import brand, netcut

REPO_ROOT = Path(__file__).resolve().parent.parent


def _cmd_serve(args: argparse.Namespace) -> int:
    from . import daemon

    daemon.serve(tick=not args.no_tick, start_live=args.live)
    return 0


def _cmd_bench(args: argparse.Namespace) -> int:
    from . import bench

    do_asr = not args.ollama_only
    do_ollama = not args.asr_only
    try:
        bench.run(asr=do_asr, ollama=do_ollama)
    except FileNotFoundError as exc:
        print(f"bench: {exc}", file=sys.stderr)
        return 2
    return 0


def _cmd_net(args: argparse.Namespace) -> int:
    action = args.action
    if action in ("cut", "restore") and not netcut.is_elevated():
        print(
            "net: needs an elevated (admin) PowerShell for firewall rules to apply.\n"
            "     Run this from an admin terminal, or use scripts\\cut-internet.ps1.",
            file=sys.stderr,
        )
        # still attempt; Windows will report failure clearly
    if action == "cut":
        res = netcut.cut()
    elif action == "restore":
        res = netcut.restore()
    else:  # status
        res = netcut.status()
        cut = bool(res.output)
        print(f"internet: {'CUT' if cut else 'allowed'} (group {netcut.group()})")
        if res.output:
            print(res.output)
        return 0 if res.ok else 1
    print(res.output or ("ok" if res.ok else ""))
    if res.error:
        print(res.error, file=sys.stderr)
    return 0 if res.ok else 1


def _port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) != 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    disp = brand.display_name()
    print(f"{disp} doctor")
    ok = True

    print(f"  python           : {sys.version.split()[0]}")

    # Whisper models
    wroot = REPO_ROOT / "models" / "whisper"
    found = sorted(p.name for p in wroot.glob("models--*")) if wroot.exists() else []
    print(f"  whisper models   : {found or 'NONE (run fetch-models)'}")
    ok = ok and bool(found)

    # Ollama
    try:
        from . import localclient

        resp = localclient.get("http://127.0.0.1:11434/api/tags", timeout=3.0)
        names = [m["name"] for m in resp.json().get("models", [])]
        print(f"  ollama           : up, models {names or 'none pulled'}")
        ok = ok and bool(names)
    except Exception as exc:
        print(f"  ollama           : NOT reachable ({exc})")
        ok = False

    # Ports
    for host, port, label in [("127.0.0.1", 7777, "dashboard"), ("0.0.0.0", 7778, "phone")]:
        free = _port_free("127.0.0.1", port)
        print(f"  port {port} ({label:<9}): {'free' if free else 'IN USE'}")

    # Mic
    try:
        import sounddevice as sd

        ins = [d["name"] for d in sd.query_devices() if d["max_input_channels"] > 0]
        print(f"  input devices    : {len(ins)} ({ins[0] if ins else 'none'}…)")
        ok = ok and bool(ins)
    except Exception as exc:
        print(f"  input devices    : query failed ({exc})")

    # Firewall / elevation
    print(f"  elevated (admin) : {netcut.is_elevated()}")
    print(f"  internet cut now : {netcut.is_cut()}")

    print(f"\n  {'READY' if ok else 'NOT READY — see NONE/NOT above'}")
    return 0 if ok else 1


def _cmd_wipe(args: argparse.Namespace) -> int:
    disp = brand.display_name()
    import shutil

    targets = []
    local = os.environ.get("LOCALAPPDATA")
    if local:
        targets.append(Path(local) / disp)
    docs = os.environ.get("USERPROFILE")
    if docs:
        targets.append(Path(docs) / "Documents" / disp)
    removed = []
    for t in targets:
        if t.exists():
            if not args.yes:
                print(f"would delete: {t}  (pass --yes to confirm)")
                continue
            shutil.rmtree(t, ignore_errors=True)
            removed.append(str(t))
    if args.yes:
        print(f"wiped: {removed or 'nothing to wipe'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    disp = brand.display_name()
    p = argparse.ArgumentParser(prog=brand.name(), description=f"{disp} — offline listening companion")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("serve", help="run the daemon (dashboard + phone server)")
    sp.add_argument("--no-tick", action="store_true", help="don't emit the P0 counter tick")
    sp.add_argument("--live", action="store_true", help="start in live caption mode (mic open) instead of counter")
    sp.set_defaults(func=_cmd_serve)

    bp = sub.add_parser("bench", help="measure ASR RTF/WER and Ollama tokens/s")
    bp.add_argument("--asr-only", action="store_true")
    bp.add_argument("--ollama-only", action="store_true")
    bp.set_defaults(func=_cmd_bench)

    np_ = sub.add_parser("net", help="cut|restore|status the laptop's internet (firewall)")
    np_.add_argument("action", choices=["cut", "restore", "status"])
    np_.set_defaults(func=_cmd_net)

    dp = sub.add_parser("doctor", help="check models, ports, mic, ollama, firewall")
    dp.set_defaults(func=_cmd_doctor)

    wp = sub.add_parser("wipe", help="delete all stored text/notes for this brand")
    wp.add_argument("--yes", action="store_true", help="actually delete (otherwise dry run)")
    wp.set_defaults(func=_cmd_wipe)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
