"""Product pages (served on the laptop dashboard; also shown as in-app sheets).

Real, specific content — About / How it works, Privacy Policy, Terms, Accessibility,
Open-source licenses (library licenses read from installed package metadata, not
guessed), and FAQ. Same design tokens, readable long-form typography.
"""

from __future__ import annotations

from . import brand

_C = {
    "fd": "#12241A", "forest": "#1F3A24", "beige": "#DDE3D3", "paper": "#EEF1E8",
    "sage": "#A9B89C", "moss": "#3D5A40", "ink": "#12241A",
}

# Models + their licenses (from each project's published license).
_MODEL_LICENSES = [
    ("OpenAI Whisper (tiny.en, base.en, small, tiny)", "MIT"),
    ("faster-whisper / CTranslate2 conversions", "MIT"),
    ("Qwen2.5-1.5B-Instruct (via Ollama)", "Apache-2.0"),
    ("nomic-embed-text v1.5 (via Ollama)", "Apache-2.0"),
    ("Piper voice en_US-lessac-medium", "MIT (voice: CC0/MIT per voice card)"),
    ("Silero VAD (bundled in faster-whisper)", "MIT"),
]
_LIB_PKGS = [
    "faster-whisper", "ctranslate2", "fastapi", "uvicorn", "httpx", "pydantic",
    "numpy", "sounddevice", "rapidfuzz", "jellyfish", "dateparser", "psutil",
    "segno", "piper-tts", "pyttsx3",
]


def _lib_licenses() -> list[tuple[str, str]]:
    import importlib.metadata as md

    out = []
    for pkg in _LIB_PKGS:
        lic = "—"
        try:
            meta = md.metadata(pkg)
            lic = meta.get("License") or "—"
            if (not lic or lic == "UNKNOWN" or len(lic) > 40):
                clf = [c for c in meta.get_all("Classifier") or [] if c.startswith("License ::")]
                if clf:
                    lic = clf[0].split("::")[-1].strip()
        except Exception:
            lic = "(not installed)"
        out.append((pkg, lic))
    return out


def _page(title: str, body: str) -> str:
    d = brand.display_name()
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{d} · {title}</title>
<style>
 body{{margin:0;background:{_C['fd']};color:{_C['beige']};
   font-family:"Host Grotesk",ui-sans-serif,system-ui,sans-serif;line-height:1.55;}}
 .wrap{{max-width:720px;margin:0 auto;padding:48px 24px 80px;}}
 a{{color:{_C['beige']};}} h1{{font-size:34px;letter-spacing:-0.02em;margin:0 0 8px;}}
 h2{{font-size:20px;margin:32px 0 8px;color:{_C['paper']};}}
 p,li{{color:{_C['beige']};font-size:16px;}} .muted{{color:{_C['sage']};}}
 .card{{background:{_C['forest']};border-radius:14px;padding:18px 20px;margin:14px 0;}}
 code{{font-family:"Fragment Mono",ui-monospace,monospace;color:{_C['sage']};}}
 table{{width:100%;border-collapse:collapse;font-size:14px;}}
 td{{padding:6px 8px;border-bottom:1px solid rgba(169,184,156,.2);}}
 .nav{{position:sticky;top:0;z-index:2;height:60px;display:flex;align-items:center;gap:10px;
   padding-top:env(safe-area-inset-top);padding-left:16px;padding-right:16px;box-sizing:content-box;
   background:{_C['fd']};border-bottom:1px solid rgba(221,227,211,.18);}}
 .nav a{{text-decoration:none;color:{_C['beige']};}}
 .nav .back{{width:40px;height:40px;border:1px solid rgba(221,227,211,.35);border-radius:11px;
   display:flex;align-items:center;justify-content:center;font-size:22px;}}
 .nav img{{width:22px;height:22px;border-radius:6px;}}
 .step{{display:flex;gap:14px;align-items:flex-start;margin:10px 0;}}
 .num{{flex:0 0 28px;height:28px;border-radius:50%;background:{_C['moss']};
   display:flex;align-items:center;justify-content:center;font-weight:600;}}
</style></head><body>
<header class="nav"><a class="back" href="/" aria-label="Back">‹</a>
<img src="/icon-192.png" alt=""><a href="/">{d}</a></header>
<div class="wrap">
<h1>{title}</h1>
{body}
</div></body></html>"""


def about() -> str:
    d = brand.display_name()
    return _page("About", f"""
<p class="muted">Every word, within earshot.</p>
<p>{d} turns the microphone on this laptop into live captions on the screens you already
own — your phone, your watch's Now Playing, a caption bar — and quietly tells you when your
name or something you care about is said. Everything runs on this machine.</p>
<h2>How it works</h2>
<div class="step"><div class="num">1</div><div><b>Hear.</b> The laptop listens through its mic. Raw audio lives only in a 30-second memory buffer and is never written to disk.</div></div>
<div class="step"><div class="num">2</div><div><b>Transcribe locally.</b> faster-whisper turns speech into text on the CPU — no cloud, no account.</div></div>
<div class="step"><div class="num">3</div><div><b>Notice moments.</b> Your name, keywords, dates and questions are flagged with the reason they matter.</div></div>
<div class="step"><div class="num">4</div><div><b>Show it.</b> Captions and alerts appear on your phone and watch over your own Wi-Fi. Cut the internet and it keeps working.</div></div>
<h2>Why offline</h2>
<p>It's other people's voices. They shouldn't be streamed to a cloud — and classrooms,
terminals and brownouts don't always have good internet. {d} needs none.</p>""")


def privacy() -> str:
    d = brand.display_name()
    return _page("Privacy Policy", f"""
<p class="muted">Plain language. Measured, not promised.</p>
<h2>What's collected</h2>
<p><b>Text only</b> — the transcript of what's heard, alerts, and notes you keep.</p>
<h2>What's never collected</h2>
<p>Raw audio (it stays in a 30-second RAM buffer and is discarded), contacts, location,
analytics, or any identifiers. {d} makes <b>no network calls</b> to anyone; the only HTTP
client refuses non-local addresses, so bytes-to-the-internet are 0 by construction.</p>
<h2>Where it's stored</h2>
<p>On this laptop only, in a local SQLite database under
<code>%LOCALAPPDATA%\\{d}\\earshot.db</code>, and notes under
<code>Documents\\{d}\\</code>.</p>
<h2>Retention</h2>
<p>Text auto-expires on the schedule you choose (1 hour / 24 hours / 7 days / keep). Default 24 hours.</p>
<h2>Sharing</h2>
<p>None. There is no server, no account, no third party.</p>
<h2>Your controls</h2>
<p>Mute stops the mic instantly. "Delete everything" wipes all stored text. You can export
your own notes and .ics. Change retention any time in Settings.</p>
<h2>Consent</h2>
<p>Tell people you're captioning, and follow local recording laws (in the Philippines, RA 4200).</p>""")


def terms() -> str:
    d = brand.display_name()
    return _page("Terms of Use", f"""
<p>By using {d} you agree to the following.</p>
<h2>Personal use</h2><p>{d} is provided for personal, non-commercial use.</p>
<h2>Consent & law</h2><p>Recording or transcribing others may be restricted where you live.
Tell people you are captioning and follow local recording laws. You are responsible for lawful use.</p>
<h2>No warranty on accuracy</h2><p>Speech recognition and translation make mistakes, especially
in noise, at a distance, or across languages. Do not rely on {d} for anything critical.</p>
<h2>Not for emergencies or records</h2><p>{d} is not an emergency service, medical or
accessibility-certified device, or a legal record. Don't use it as one.</p>
<h2>As-is</h2><p>The software is provided "as is", without warranty of any kind.</p>""")


def accessibility() -> str:
    d = brand.display_name()
    return _page("Accessibility", f"""
<p>{d} is built first for Deaf and hard-of-hearing people — live captions of the room,
on a glanceable screen, without holding up a phone.</p>
<h2>Built in</h2>
<ul>
<li><b>Text size</b> — a slider from 16 to 40 px; your choice is remembered.</li>
<li><b>High contrast</b> — beige on deep forest, large weight for the current line.</li>
<li><b>Right-to-left</b> — Arabic renders RTL with an Arabic-capable font.</li>
<li><b>Screen-reader labels</b> — controls are labelled; the live region announces new lines.</li>
<li><b>Quiet mode</b> — "Listen for me" shows only what matters, no scrolling wall of text.</li>
</ul>
<p class="muted">Tell us what would help: use Send feedback in Settings.</p>""")


def licenses() -> str:
    rows = "".join(f"<tr><td>{n}</td><td class='muted'>{l}</td></tr>" for n, l in _MODEL_LICENSES)
    libs = "".join(f"<tr><td>{n}</td><td class='muted'>{l}</td></tr>" for n, l in _lib_licenses())
    return _page("Open-source licenses", f"""
<p>{brand.display_name()} is built on open-source models and libraries. Library licenses
below are read from each installed package's metadata.</p>
<h2>Models</h2><div class="card"><table>{rows}</table></div>
<h2>Libraries</h2><div class="card"><table>{libs}</table></div>
<p class="muted">{brand.display_name()} itself: MIT. Fonts: Host Grotesk & Fragment Mono (SIL OFL 1.1).</p>""")


def faq() -> str:
    d = brand.display_name()
    qa = [
        ("Does it need internet?", f"No. All speech recognition, alerts, summaries and translation run on this laptop. {d} makes no network calls; cut the internet and it keeps working. You only need internet once, to install the models."),
        ("Does it record audio?", "No. Raw audio stays in a 30-second memory buffer and is never written to disk. Only text is stored, and it auto-expires."),
        ("Which languages?", "English is the priority and most accurate. Tagalog and Arabic are supported; pick the spoken language (no auto-guessing). You choose the language, so it never mislabels."),
        ("Does it work far away?", "It hears what the laptop's mic hears. A closer or array mic helps a lot; " + d + " picks the best input device automatically. Very distant/quiet speech in a loud room is hard — accuracy drops with distance."),
        ("Battery / RAM?", "About 1.8 GB of RAM (Earshot + the local models), which unload after a few minutes idle. Plug in for long sessions; CPU transcription is the main draw."),
        ("How do I delete everything?", "Settings → Privacy → Delete everything wipes all stored text, or run <code>earshot wipe --yes</code>. Mute stops the mic instantly any time."),
    ]
    body = "".join(f"<div class='card'><h2 style='margin-top:0'>{q}</h2><p>{a}</p></div>" for q, a in qa)
    return _page("FAQ", body)


RENDERERS = {
    "about": about, "privacy": privacy, "terms": terms,
    "accessibility": accessibility, "licenses": licenses, "faq": faq,
}
