# 02 · Design system: Editorial Forest v3 · Earshot (Apple-calm)

> `Earshot` = `tokens.json → brand.name` (currently "earshot", display "Earshot"; may become "Kinig"). Never type the name into components; read the token. The wordmark/lockups are generated from it (`design/_src/`).

**Mood:** quiet, confident, product-first, like an apple.com product page dressed in forest and beige. One sans family does everything. Big short headlines, lots of air, real product shots (watch, lock screens, the caption bar). Emphasis comes from **weight and tone**, never italics or a second typeface.
**Surfaces:** caption bar (Tkinter overlay, primary) · phone page = **one plain HTML file** · dashboard = **Vite + React + Tailwind + shadcn** (dark), served by the daemon on 127.0.0.1 · landing page = cut (README + screenshots instead).
**Never:** purple, blue (except `listen-glow`, §1), gradients (except the listening glow blur and the nav backdrop blur), neon, glassmorphism cards, emoji-as-icons, AI glossy 3D, stock illustrations, serif fonts, italics, Inter / Geist / Instrument Serif / Satoshi / General Sans / Space Grotesk / DM Sans / Manrope / Poppins / Roboto. Pure `#000`/`#FFF` only in mono logo exports.

Tokens live in `design/tokens.json` (single source; CSS vars, Tailwind theme, Python `cards.py` and `bar.py` read it). Reference renders: `design/brand-sheet.png`, `design/mock-watch-lockscreen.png`, `design/tiles/*.png`. **When this doc and a render disagree, the doc wins. When the doc is silent, copy the render.**

---
## 1. Color

| Token | Hex | Tailwind | Role |
|---|---|---|---|
| `forest` | `#1F3A24` | `forest` | Primary brand, dark surfaces, primary buttons |
| `forest-deep` | `#12241A` | `forest-deep` | Darkest bg / ink on light |
| `moss` | `#3D5A40` | `moss` | Hover / secondary dark / idle |
| `sage` | `#A9B89C` | `sage` | Muted, borders on dark, working |
| `beige` | `#DDE3D3` | `beige` | Primary light surface, text on dark |
| `paper` | `#EEF1E8` | `paper` | Lightest surface, cards on beige |
| `ink-muted` | `#5B6B5C` | `ink-muted` | Secondary text on light |

### Listening glow (new, logo only)
`listen-glow` **#7FB3D5** — soft blue, used **only** as the blurred glow inside the logo's curl in the LISTENING state (logo-listening.svg, the listening tile, the caption bar's live dot). Never a fill, never text, never anywhere else. This is the single exception to "no blue".
`crescent` **#D9C7A0** — the warm inner curl of the mark. Logo only (and its swatch).

### State colors — muted, earthy accents (ONLY for listening states — tile header band, status dots, badges, state labels). Never large fills in UI, never decoration.

Each state has an **accent** (dots, bars, bands, labels on dark) and an **-ink** variant for text on `paper`/`beige` (AA ≥ 4.5).

| State | Color token | Accent hex | Text-on-light hex | Shape | Word |
|---|---|---|---|---|---|
| `WORKING` | `sage` | `#A9B89C` | `#5B6B5C` (ink-muted) | ▶ | WORKING |
| `NEEDS_YOU` | `needs-you` (brass) | `#C9A45C` | `needs-you-ink` `#7A5826` | ◆ | NEEDS YOU |
| `DONE` | `approved` (fern) | `#8FA876` | `approved-ink` `#566B42` | ✓ | DONE |
| `STUCK` | `denied` (clay) | `#C47A62` | `denied-ink` `#96432F` | ■ | STUCK |
| `RISK` | `denied` (clay) | `#C47A62` | `denied-ink` `#96432F` | ■ | AT LAPTOP |
| `PAUSED` | `moss` | `#3D5A40` | `forest-deep` | ‖ | PAUSED |

State is **never color only** — always shape + word. Check grayscale: ◆ ▶ ✓ ■ ‖ must stay distinguishable.
`WORKING` = sage with a 2 s pulse. `NEEDS_YOU` = brass dot breathes 1.2 s.

### Modes

| Mode | Where | Bg | Cards | Text | Borders |
|---|---|---|---|---|---|
| **Light (default)** | Landing | `paper` / `beige` | `paper` | `forest-deep` | `forest` @ 12% |
| **Dark** | Dashboard | `forest-deep` | `forest` | `beige` | `sage` @ 40% |

### shadcn variable mapping

**Light (landing):**
```
--background: paper #EEF1E8
--foreground: forest-deep #12241A
--card: paper #EEF1E8
--card-foreground: forest-deep #12241A
--muted: beige #DDE3D3
--muted-foreground: ink-muted #5B6B5C
--border: forest #1F3A24 at 12%
--primary: forest #1F3A24
--primary-foreground: beige #DDE3D3
--secondary: beige #DDE3D3
--secondary-foreground: forest-deep #12241A
--accent: sage #A9B89C
--accent-foreground: forest-deep #12241A
--destructive: denied-ink #96432F
--ring: forest #1F3A24
--radius: 8px
```

**Dark (dashboard):**
```
--background: forest-deep #12241A
--foreground: beige #DDE3D3
--card: forest #1F3A24
--card-foreground: beige #DDE3D3
--muted: moss #3D5A40
--muted-foreground: sage #A9B89C
--border: sage #A9B89C at 40%
--primary: beige #DDE3D3
--primary-foreground: forest-deep #12241A
--secondary: moss #3D5A40
--secondary-foreground: beige #DDE3D3
--accent: sage #A9B89C
--accent-foreground: forest-deep #12241A
--destructive: denied #C47A62
--ring: beige #DDE3D3
--radius: 8px
```

### Approved text / bg pairs (WCAG AA)

| Text | On | Notes |
|---|---|---|
| `forest-deep` | `paper`, `beige`, `sage` | Body + headlines on light |
| `ink-muted` | `paper`, `beige` | Secondary only |
| `beige` | `forest`, `forest-deep`, `moss` | Body on dark |
| `sage` | `forest-deep`, `forest` | Muted on dark |
| `needs-you` / `approved` / `denied` | `forest-deep` (≥ 4.8) | State labels on dark |
| `needs-you-ink` / `approved-ink` / `denied-ink` | `paper` (≥ 5) | State labels on light |
| `forest-deep` | `needs-you`, `approved`, `denied`, `sage`, `beige` | Small text on a state band (tiles only) |

Banned fills for body text: never put `ink-muted` on `moss`, never put `sage` on `beige`.

---

## 2. Typography

**Two families, nothing else.** Apple sets everything in one neo-grotesk (SF Pro), so we do the same:

| Role | Family | License | Weights used | Files |
|---|---|---|---|---|
| Display + UI + body | **Host Grotesk** (Element Type, 2024) | SIL OFL 1.1 | 400 · 500 · 600 (variable 300–800) | `design/fonts/HostGrotesk-VariableFont_wght.ttf` |
| Code, commands, logs, data | **Fragment Mono** (Wei Huang, 2022; Helvetica-style mono) | SIL OFL 1.1 | 400 only (+ italic, unused) | `design/fonts/FragmentMono-Regular.ttf` |

Loading: self-host both from `design/fonts/` via `@font-face` (`font-display: swap`). The phone page may use Google Fonts `family=Host+Grotesk:wght@400;500;600&family=Fragment+Mono`. Fallbacks: `"Host Grotesk", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif` / `"Fragment Mono", ui-monospace, "SF Mono", Consolas, monospace`. Enable `-webkit-font-smoothing: antialiased` on dark surfaces only.

**Why:** Host Grotesk is a quiet neo-grotesk, close to SF Pro in proportion. It's new enough that it isn't the default "AI startup" font yet, and it holds up at 80 px and 13 px. Fragment Mono is built on a Helvetica skeleton, so the mono matches the sans instead of fighting it. Alternates if this ever needs to change: (B) Schibsted Grotesk + IBM Plex Mono, (C) Hanken Grotesk + Martian Mono. See `design/type-options.png`.

### Type scale (Apple ratios, tracked tighter because Host Grotesk has no optical "Display" cut)

Sizes are desktop / ≤1068 px / ≤734 px. Line-height is unitless, tracking is in em.

| Token | Size | LH | Tracking | Weight | Use |
|---|---|---|---|---|---|
| `hero` | 80 / 64 / 48 | 1.05 | −0.032 / −0.028 / −0.022 | 600 | Landing hero headline only (one per page) |
| `display` | 56 / 48 / 32 | 1.07 | −0.025 / −0.022 / −0.015 | 600 | Section headlines |
| `headline` | 40 / 32 / 28 | 1.1 | −0.02 / −0.015 / −0.01 | 600 | Bento tile headlines, dashboard Now Playing title |
| `title` | 28 / 24 / 21 | 1.14 | −0.015 | 600 | Card titles, footer CTA |
| `eyebrow` | 21 / 19 / 17 | 1.19 | −0.005 | 600 | Section eyebrow (the word above a headline) |
| `intro` | 21 / 19 / 17 | 1.38 | −0.005 | 400 | Lead paragraph under a headline, `ink-muted` / `sage` |
| `body` | 17 | 1.47 | −0.01 | 400 | Default body (Apple's 17 px) |
| `body-sm` | 14 | 1.43 | −0.005 | 400 | Dense copy, table cells, tooltips |
| `ui` | 13 | 1.38 | 0 | 500 | Buttons (small), tabs, nav links, labels |
| `caption` | 12 | 1.33 | 0 | 400 | Footnotes, legal, image captions |
| `mono` | 14 | 1.45 | 0 | 400 | Commands, logs |
| `mono-sm` | 12 | 1.4 | 0 | 400 | Timestamps, table data, keycaps (11) |
| `overline` | 11 | 1.3 | +0.10 em, UPPERCASE | 400 mono | State labels, tile chrome, tiny metadata. Never body. |

**Headline emphasis (Apple style).** In this doc, *asterisks* in copy mean the muted-tone phrase, never italics. one sentence, two tones. The first phrase is in the ink color, the second phrase is in `ink-muted` (light) / `sage` (dark), same weight. Example: `Your fix,` **forest-deep** + `now playing.` **ink-muted**. No italics, no colored gradients, no underline. At most one tone switch per headline.

**Rules:** headlines end with a period. Max 2 lines on desktop (hero ≤ 26 characters per line). Body max width **64 ch** (≈ 620 px at 17 px). Never set Host Grotesk under 12 px or Fragment Mono under 11 px. Never use weight 700+ or 300. Numbers in tables: `font-variant-numeric: tabular-nums`.

---

## 3. Logo — FINAL (Oct 9, traced from Fathi's mark)

**Mark:** an ear / sound curl: a forest teardrop body that curls into a round inner lobe, a warm **crescent** (`#D9C7A0`) inside the upper curl, and a **hollow** (transparent: the background shows through) between crescent and lobe. Two colours only. Traced from Fathi's flat PNG with potrace into smooth béziers (`design/_src/trace.py`), visually compared side by side with the source.
**Listening glow (optional, state effect only):** a soft `listen-glow` #7FB3D5 blur sitting in the hollow (`logo-listening.svg`). Use only while LISTENING (listening tile, caption bar live dot). Never on static brand uses (README, slides, favicon).
**Colour rules:** on light (`paper`/`beige`): body `forest`, crescent `crescent`. On dark (`forest`/`forest-deep`/`moss`): body `paper`, crescent `crescent`. Mono (`logo-mono.svg`, `currentColor`): body only, crescent cut out (it becomes background), for favicons at 16 px, embossing, single-colour print.
**Wordmark:** `earshot` lowercase, Host Grotesk 500, −0.025 em, outlined (`wordmark.svg`, lockups). Lockup: mark height = 1, wordmark x-height = 0.40, gap = 0.30, wordmark baseline at 0.80 of mark height.
**Clear space:** ¼ of the mark height on all sides. **Min size:** mark 16 px (use mono), lockup 96 px wide.
**Don't:** recolour outside the rules, add outlines/shadows, rotate, use the glow statically, stretch, put the 2-colour mark on mid-tones (`sage`/`moss` → use the dark rule).

### Files in `design/`
| File | Use |
|---|---|
| `logo.svg` | 2-colour mark, light backgrounds |
| `logo-mono.svg` | single colour, `currentColor` |
| `logo-listening.svg` | with the glow, LISTENING only |
| `logo-on-paper.svg` · `logo-on-forest-deep.svg` | mark with background, for slides/social |
| `lockup-light.svg` · `lockup-dark.svg` · `wordmark.svg` | mark + wordmark (outlined) |
| `favicon.svg` · `favicon.ico` (16/32/48) · `icon.svg` · `icon-fullbleed.svg` · `icon-512.png` · `icon-192.png` · `apple-touch-icon.png` | app/web icons (paper square, 22 % radius) |
| `tiles/*.png` + `tiles/*.html` | Now Playing artwork per state (§9) |
| `brand-sheet.png` / `@2x` / `.pdf` | one-page brand sheet |
| `mock-watch-lockscreen.png` | reference mock: caption as Now Playing on iPhone lock screen + Garmin + laptop caption bar |
| `fonts/` | Host Grotesk (variable) + Fragment Mono + OFL licenses |
| `_src/` | regeneration scripts (rename = one variable) |

## 4. Layout system (from apple.com, measured, see §16)

| Token | Value | Source pattern |
|---|---|---|
| Breakpoints | **large > 1068 px**, **medium 735–1068**, **small ≤ 734** (+ `xlarge ≥ 1441` for hero media only) | apple.com `@media (max-width:1068px)` / `(max-width:734px)` |
| Viewport content | `width: 87.5%` (small: `calc(100% - 48px)`), centered | `.viewport-content{width:87.5%}` |
| Text column max | **980 px** | local nav content max-width 980 |
| Wide grid max | **1260 px** (bento, galleries) | `--global-content-max-width:1260px` |
| Hero media max | **1680 px** | `--global-content-max-width-hero:1680px` |
| Section padding (top & bottom) | **160 / 128 / 96 px** | `--global-section-padding` |
| Headline → intro gap | 20 px (all sizes) | |
| Intro → content (media/grid) | 64 / 56 / 48 px | |
| Grid | 12 cols, gutter **24 px** (small: 4 cols, gutter 16) | |
| Bento gap | **24 / 20 / 16 px** | |
| Base unit | 4 px; allowed steps 4, 8, 12, 16, 20, 24, 32, 40, 48, 56, 64, 80, 96, 128, 160 | |

Alignment: landing section headers are **center-aligned** (eyebrow, headline, intro, link) unless the section is a two-column split, where they're left-aligned. Dashboard is always left-aligned.

## 5. Radius & borders

| Token | Value | Use |
|---|---|---|
| `pill` | 980 px | Landing CTAs + local-nav "Install" button only |
| `tile` | 28 px | Landing bento tiles, device-shot containers (Apple tile radius) |
| `card` | 20 px | Dashboard cards (Now Playing card, Up next, Remotes) |
| `control-lg` | 14 px | 56–72 px phone controls, artwork inside cards |
| `control` | 8 px | 32/40 px buttons, inputs, selects, code blocks (10 px) |
| `badge` | 6 px | Badges, keycaps (5 px) |
| `icon` | 22 % | App icon |
| `full` | 50 % | Status dots only |

**Concentric rule (HIG):** inner radius = outer radius − padding. A 240 px artwork inside a 20 px card with 28 px padding gets 14 px.
Borders: 1 px hairlines only. Light: `forest` @ 12%. Dark: `sage` @ 14% (cards) / 18% (top bar) / 40% (inputs, secondary buttons). Use inset `box-shadow: inset 0 0 0 1px …` on rounded elements so the corners stay crisp. **One** real shadow, for overlays only: `0 24px 48px rgba(18,36,26,.25)`.

## 6. Iconography

Lucide, stroke **1.5**, `currentColor`, 16 px in text, 20 px in buttons, 24 px in nav/landing feature lists. Media transport glyphs (⏮ ⏯ ⏭) are **filled** custom SVGs (as in `mock-watch-lockscreen.png`), because Apple's Now Playing uses filled glyphs. State shapes ◉ ◆ ▶ ‖ □ (+ ✓ for bookmarks) are the only other custom glyphs. No emoji, no duotone icons, no icon in every heading.

## 7. Imagery

**Decision: the dithered engraving illustration is dropped.** Apple-style pages sell with the product itself, and our product is a lock screen, a watch face and a dashboard. A second visual language (engravings) would fight the device shots. A generated engraving is also exactly the "AI art" look Fathi wants to avoid. Every image slot is one of:

1. **Device shots:** real screenshots of Earshot placed in simple flat device frames (iPhone: 54 px outer radius at 300 px wide, 10 px bezel `#0B130E`, Dynamic Island 96×28; Windows: 16:10 screen with a 12 px `#0B130E` bezel and 10 px radius; watch: circular 1:1 screen, 14 px bezel). Wallpaper inside device frames = flat `forest` or `forest-deep`. No glare, no reflections, no 3D tilt, no hands.
2. **Now Playing tiles** (`design/tiles/*.png`) as artwork.
3. **UI crops** of the dashboard at 1× or 2×, sitting on a `tile` container with 40 px padding.
4. **The film** (Saturday video). Poster frame = the Garmin showing a live caption.

Framing: device centered horizontally. On the hero the bottom of the device is cropped by the fold (Apple marquee crop). Inside bento tiles, devices bleed off the tile's bottom edge by 15–25% of their height. Image aspect slots are listed per section in §10.

## 8. Motion

| Kind | Duration | Easing |
|---|---|---|
| Hover / press | 120 ms | `cubic-bezier(0.4, 0, 0.6, 1)` (Apple local-nav curve) |
| UI (tabs, popovers, queue reorder) | 240 ms | same |
| Nav backdrop / curtain | 320 ms | same |
| Scroll reveal | 600 ms opacity 0→1 + translateY 24→0 | `cubic-bezier(0, 0, 0.5, 1)` (apple.com) |
| Working pulse | 2 s loop, opacity 1↔0.45 | linear |
| Needs-you breath (dot) | 1.2 s loop, scale 1↔1.35 | ease-in-out |

Scroll reveal: each section's header + media reveal **once** when 20% visible. Stagger children 80 ms, max 4 children. Never reveal body copy word by word. No parallax, no scroll-jacking, no pinned scroll sequences, no bounce, no confetti, no Lottie.
`prefers-reduced-motion: reduce` → no reveal (show immediately), no pulse/breath (static dot), crossfades ≤ 120 ms.

---

## 9. State artwork tiles (Now Playing album art)

512 × 512 PNG, rendered once per state (+ cache-bust `?v=`). Must read at 96 px. The watch shows title/artist text only.
**Layout (same editorial "book cover" as v2):** base fill · header band y 0–80 in the state accent with Fragment Mono 11 px caps `Earshot` left and `NO. 0X — NOW PLAYING` right · crop marks · mark centered, 190 px tall, top 112 (dark tiles use the dark colour rule; LISTENING adds the glow) · state shape + word, Fragment Mono 21 px caps +0.16 em at y 326 · subline Host Grotesk 14 px @ 62 % at y 366 · hairline at bottom 80 · bottom row: Fragment Mono 14 caption snippet left, time right @ 55 %.
| State | Base | Band | Ink | Label | Shape | Word |
|---|---|---|---|---|---|---|
| LISTENING | `forest` | `sage` | `beige` | `sage` | ◉ ring + dot | LISTENING |
| ALERT | `paper` | `needs-you` #C9A45C | `forest-deep` | `needs-you-ink` | ◆ | HEARD YOUR NAME (or the alert type) |
| CATCH_UP | `forest-deep` | `approved` #8FA876 | `beige` | `approved` | ▶ | CATCH ME UP |
| MUTED | `moss` | `beige` | `beige` | `beige` | ‖ | MUTED |
| OFFLINE | `beige` | `sage` | `forest-deep` | `forest` | □ | OFFLINE · ALL LOCAL |
ALERT is the only light-on-dark-lock-screen "pop" tile, on purpose. `MIC_ERROR` has no tile (caption bar + dashboard only, `denied` accent).
**Track text:** title = the current caption line (30–40 chars) or the alert line; artist = the previous line or the alert type; album = `Earshot · <mode>`.

---
## 10. Caption bar (laptop, primary surface)
- Tkinter borderless, always-on-top window, bottom-center, width `min(960, 70 % of screen)`, height 112, radius 14 (rounded via region), background `forest-deep` @ 94 %, padding 14 × 18. Draggable; position remembered.
- Row 1 (Fragment Mono 10 px, +0.06 em, caps, `sage`): left = state dot (7 px; LISTENING = `listen-glow` with a 2 s soft pulse, ALERT = `needs-you`, MUTED = `beige` outline, MIC_ERROR = `denied`) + `LISTENING · <room/mode> · EN`; right = `0 BYTES SENT · 09:41` (live counter from the privacy panel, never a static string).
- Row 2: previous line, Host Grotesk 14 px `sage`. Row 3: current line, Host Grotesk 600 20 px `beige`, partial words at 60 % opacity until committed.
- ALERT: 3 px left bar `needs-you`, row 1 becomes `◆ HEARD YOUR NAME`, one 600 ms flash of the background to `forest`, chime. MUTED: rows 2–3 replaced by "Muted · not listening" in `beige`, whole bar 70 % opacity. Mode badges: `TL→EN` in a 20 px badge.
- Hover reveals three 32 px ghost buttons on the right: Bookmark, Catch me up, Mute (same actions as Next/Previous/Pause).
- Reference: `design/mock-watch-lockscreen.png` (laptop panel).

## 11. Dashboard (dark, Vite + React + shadcn, 127.0.0.1:7777)
### 11.1 Frame
`forest-deep` background, top bar 56 px: mark 20 px + `Earshot` 17/600; tabs `Live · Alerts · Recall · Notes · Privacy` (14 px `sage`, active `beige` + 2 px underline); right: state pill (dot + word) + **Mute [M]** secondary button + **Cut internet** switch (only enabled when elevated; tooltip explains). Content grid `1fr 360px`, gap 24, padding 32, max 1440.
### 11.2 Live (`/`)
- Left: **live transcript** card (radius 20, padding 28): lines grouped by minute with Fragment Mono 12 timestamps in a 64 px gutter; current partial at 60 % opacity; alert lines get a 3 px `needs-you` left bar + ◆; bookmarks get a `approved` ✓ in the gutter. Auto-scroll pinned unless the user scrolls up ("Jump to live ↓" pill-free button, r 8).
- Right rail: **Now playing** card (the tile 120 px + title/artist exactly as sent to the watch, "sent 1.2 s ago" from real timestamps) · **Catch me up** card (button + last summary with its source lines collapsible) · **Bookmarks** list (time + line).
### 11.3 Alerts (`/alerts`)
Table: Time · Type badge (`Your name`, `Deadline`, `Quiz`, `Travel`) · Line (with the keyword in 600 weight) · Source (`keyword` / `keyword + brain`) · Jump. Settings strip on top: keyword chips (add/remove, your name + variants), fuzzy threshold slider, cooldown.
### 11.4 Recall (`/recall`)
Search input 48 px, r 14, placeholder "Ask what was said… e.g. what did ma'am say about the midterm?" + mic button (push-to-talk). Answer card: answer 21/600, **exact quote** in a mono block with the timestamp chip ("10:42 · Room 304"), "Jump to transcript ›"; "Not found in your transcripts" state shows the closest excerpt. Below: top 5 excerpts with similarity bars (1.5 px `sage`, no numbers unless measured).
### 11.5 Notes (`/notes`)
Session list left (date, duration, room), right: Summary bullets, To-dos (checkboxes), Deadlines table (what · when as said · resolved date or "date unclear" · quote), buttons "Download .ics" and "Copy markdown".
### 11.6 Privacy (`/privacy`) — also a compact card on Live
Rows (label 13 `sage`, value Fragment Mono 13 `beige`, tabular-nums): `Microphone` (Listening / Muted, with the Mute button) · `Raw audio on disk` `none — RAM only, last 30 s` · `Text kept for` (auto-expire select) · `Bytes sent to the internet by Earshot` (live counter) · `Internet connections (Earshot + Ollama)` (live, sampled) · `Internet reachable` (yes/no from the probe) · `Models` (`base.en · qwen2.5:3b · nomic-embed-text` from the running engines) · `Delete everything` (danger button, dialog). Caption under: "Measured live on this laptop." Values show "—" until measured.
### 11.7 States
Loading/models warming (skeleton + "Loading speech model…"), MIC_ERROR (inline banner, `denied` left bar, "Microphone unavailable. Check Windows privacy settings."), offline (calm `moss` bar "Internet cut · everything still runs here", never red), reconnecting phone ("iPhone reconnecting…").
### 11.8 Keyboard
`M` mute/unmute · `B` bookmark · `C` catch me up · `R` replay last line · `/` recall search · `?` shortcuts. 500 ms repeat filter like the buttons.

## 12. Phone page (`web/index.html`)
Background `forest-deep`, text `beige`, safe-area padding. **Start screen:** mark 56 px (listening variant), title 28/600 "`Earshot` remote", 15 px `sage` "Keep this tab open in Safari. Don't add to Home Screen.", button "Start" (56 px, r 14, `beige`). **Main:** top bar (connection dot + "live"/"reconnecting…"), artwork = state tile (min(100vw−40, 360), r 14), current line 22/600 (2 lines), previous line 15 `sage`, overline state + time, then three 72 px controls: **Catch me up** (⏮), **Mute / Listen** (‖ / ▶, `moss`), **Bookmark** (⏭, `beige`). "Tap to resume" overlay if the audio session stopped.

## 13. Components

### Button
| Variant | Size | Height / padding / radius / type | Rest | Hover | Active | Focus | Disabled |
|---|---|---|---|---|---|---|---|
| `cta` (landing only) | lg | 44 min, 12×22, pill, 17/500 | `forest` fill, `paper` text | fill `forest-deep` | scale .98 | 2 px ring `forest`, 2 px offset | opacity .42 |
| `cta` | sm (nav) | 24, 4×11, pill, 12/500 | same | same | same | same | same |
| `link` (landing) | — | 17/500, `forest`, " ›" suffix | no underline | underline 1 px, offset 3 | opacity .7 | ring | .42 |
| `primary` (app) | md / lg | 32 (8×12, r 8, 13/500) / 40 (r 8, 14/500) | dark: `beige` fill, `forest-deep` text | fill `paper` | inset 1 px `forest-deep` @ 20% | 2 px `beige` ring | .36 |
| `secondary` | md / lg | same | transparent, inset 1 px `sage` @ 40%, text `beige` | bg `moss` @ 40% | bg `moss` @ 60% | ring | .36 |
| `ghost` | md | same | no border | bg `moss` @ 40% | @ 60% | ring | .36 |
| `control-xl` (phone page Catch me up / Mute / Bookmark) | xl | 72 (r 14, 17/600) | see §12 | `paper` fill / `moss` @ 60% | scale .99 | ring | .36 |

**Pill decision:** pills are used **only** on the marketing page (CTA + nav Install). It's the most recognizable Apple pattern and reads as consumer-premium. Inside the app, controls are 8/14 px rounded rectangles, because pills waste width in dense UI and turn into "AI dashboard" look. Labels sentence case. Max one `cta`/`primary` per view region.

### Others
| Component | Spec |
|---|---|
| **Input** | 40 px, r 8, padding 0 12, 14 px. Dark: bg `forest-deep`, inset 1 px `sage` @ 40%, placeholder `sage` @ 70%. Hover border @ 60%. Focus: 2 px `beige` ring. Error: border `denied`, 12 px message below in `denied`. Disabled .36. |
| **Segmented control** | 32 px, r 8, track `forest-deep` inset hairline, active segment `moss` with `beige` text, 240 ms slide. |
| **Badge** | 20 px, r 6, padding 0 8, mono 11 caps +0.06 em. State badges: transparent bg, inset 1 px state color @ 50%, text state color (on light: the `-ink` color), always shape + word. |
| **Card** | See §5/§11. Padding 20 (dense) / 28 (feature). No drop shadow. |
| **Table** | §11.4. Sticky header on scroll with `forest` bg. Zebra stripes forbidden. |
| **Toast** | Bottom-center, 48 px tall, r 14, `forest` bg, inset hairline, 3 px left bar in the state color, 14 px text + optional ghost action, auto-dismiss 4 s, slide up 16 px 240 ms. Max 2 stacked. |
| **Dialog** | Max-width 480, r 20, padding 28, `forest` bg, the overlay shadow, backdrop `forest-deep` @ 70% (no blur). Title 21/600, body 14 `sage`, actions right-aligned (secondary then primary). Esc closes. |
| **Tooltip** | 28 px, r 6, padding 0 8, `paper` bg + `forest-deep` 12 px text (dark UI), delay 500 ms, no arrow. Includes the keycap when the control has a shortcut. |
| **Keycap** | min 20×20, r 5, mono 11, inset 1 px currentColor, opacity .7. |
| **Tabs** | §11.1 underline style. Never pill tabs. |
| **Local nav** | §10.0. |
| **Status dot** | 7 px circle; live = `approved`, working = `sage` pulse, needs-you = `needs-you` breath, offline = `denied`. |

---

## 14. Copywriting
- Apple cadence: short declarative headlines with a period, one tone switch, plain intros. No "revolutionary / seamless / supercharge / AI-powered".
- Product name from the token: "Earshot" in prose (capitalized), `earshot` in the wordmark/CLI/URLs.
- Buttons: "Start", "Mute", "Listen", "Bookmark", "Catch me up", "Replay", "Cut internet", "Restore internet", "Download .ics", "Delete everything".
- Never claim the watch vibrates. Never show a number that isn't measured.
| Section | Eyebrow | Headline | Intro |
|---|---|---|---|
| Hero | Earshot | Hear what matters. *Offline.* | A private companion that listens on your laptop and puts captions, your name and a quick catch-up on the screens you already own. |
| Problem | The problem | You zoned out. *Your name didn't.* | The quiz date, the deadline, the gate change. Said once, out loud, while you weren't listening. |
| How | How it works | It listens. *Your watch shows it.* | Speech is transcribed on the laptop. Each line becomes the Now Playing track. |
| Local | Local AI | Nothing leaves *the laptop.* | Speech recognition, alerts and summaries run on a 16 GB laptop. Cut the internet and it keeps listening. |
| Privacy | Privacy | Mute is *one press.* | Audio lives in memory for 30 seconds and is gone. Only text is kept, and it expires. |
| Recall | Recall | Ask what was *said.* | Find the exact quote and the minute it was said. |
(*asterisks* = the muted-tone phrase, not italics.)

## 15. Pre-ship checklist
- [ ] Only Host Grotesk + Fragment Mono load. No hard-coded hex; tokens only. The brand name comes from the token.
- [ ] Logo used per §3 colour rules; glow only in LISTENING.
- [ ] Every state = colour + shape + word on tiles, bar, dashboard, phone.
- [ ] Privacy values are live or "—". Mute is visible on every surface within 1 s.
- [ ] Compare against `mock-watch-lockscreen.png` and `brand-sheet.png` before calling a screen done.

## 16. References (sources these rules came from)

- apple.com AirPods Pro page and its stylesheet: https://www.apple.com/airpods-pro/ · https://www.apple.com/v/airpods-pro/t/built/styles/overview.built.css (type ramp 96/80/64/56/48/40/32/28/24/21/17/14/12 with tracking −0.015 → +0.012 em, line-heights 1.05–1.47; breakpoints 1068/734; `.viewport-content` 87.5%; content max 1260, hero 1680; section padding 160/128/96; pill radius 980 px; CTA padding 12×22 at 17 px; tile radius 28).
- Apple local nav stylesheet: https://www.apple.com/ac/localnav/9/styles/ac-localnav.built.css (height 52/48, content max-width 980, padding 22/16, title 21/19 px 600, curtain transition 320 ms `cubic-bezier(0.4,0,0.6,1)`).
- Apple Watch page: https://www.apple.com/watch/
- Apple HIG, Typography: https://developer.apple.com/design/human-interface-guidelines/typography (default 17 pt / min 11 pt on iOS; avoid light weights; emphasize with weight/size/color).
- Apple HIG, Layout: https://developer.apple.com/design/human-interface-guidelines/layout (safe areas, standard margins, consistent grid spacing).
- Apple HIG, Live Activities: https://developer.apple.com/design/human-interface-guidelines/live-activities (14 pt Lock Screen margin, concentric corner radii, compact glanceable content, colors that hold up on personalized lock screens).
- Apple HIG, Playing audio: https://developer.apple.com/design/human-interface-guidelines/playing-audio (Now Playing view conventions).
- Linear, "How we redesigned the Linear UI (part II)": https://linear.app/now/how-we-redesigned-the-linear-ui (inverted-L app chrome, reduced chrome color, display cut for headings, alignment work in sidebar/tabs). That's why the dashboard has a quiet top bar instead of a colored sidebar.
- Things by Cultured Code: https://culturedcode.com/things/ (two-word headlines like "Simply Powerful", platform list per device). That's the model for the Surfaces copy.
- teenage engineering OP–1 field: https://teenage.engineering/products/op-1 (lowercase voice, short headline then a dense factual paragraph, spec lists). That's the model for the Rules table and the mono metadata.
- Fonts: Host Grotesk https://fonts.google.com/specimen/Host+Grotesk · license https://github.com/google/fonts/blob/main/ofl/hostgrotesk/OFL.txt; Fragment Mono https://fonts.google.com/specimen/Fragment+Mono · https://github.com/google/fonts/blob/main/ofl/fragmentmono/OFL.txt.
