import json, os, subprocess
NAME = os.environ.get("BRAND_NAME", "earshot")      # change to "kinig" and re-run to rebrand
NAME_CAP = NAME.capitalize()
D = "../earshot-docs/design"
P = json.load(open("paths.json")); W = json.load(open("wordmark.json"))
C = dict(forest="#1F3A24", forest_deep="#12241A", moss="#3D5A40", sage="#A9B89C", beige="#DDE3D3",
         paper="#EEF1E8", ink_muted="#5B6B5C", crescent="#D9C7A0", glow="#7FB3D5",
         alert="#C9A45C", alert_ink="#7A5826", fern="#8FA876", fern_ink="#566B42", clay="#C47A62", clay_ink="#96432F")
X0, Y0, X1, Y1 = 65, 42, 373, 529; MW, MH = X1 - X0, Y1 - Y0
def mark_svg(body=C["forest"], cres=C["crescent"], glow=False, pad=0, attrs=""):
    g = ""
    if glow:
        g = (f'<defs><filter id="gl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="16"/></filter></defs>'
             f'<ellipse cx="236" cy="258" rx="44" ry="50" fill="{C["glow"]}" fill-opacity=".75" filter="url(#gl)"/>')
    cr = f'<path fill="{cres}" d="{P["beige"]}"/>' if cres else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{X0-pad} {Y0-pad} {MW+2*pad} {MH+2*pad}" {attrs}>'
            f'{g}{cr}<path fill="{body}" fill-rule="evenodd" d="{P["green"]}"/></svg>')
def mono_svg(color="currentColor"):
    return mark_svg(body=color, cres=None)
DARK = dict(body=C["paper"], cres=C["crescent"])   # mark on forest-deep
def wordmark_g(color, x, y, h):  # h = x-height px
    s = h / W["xh"]; return f'<g transform="translate({x - W["bounds"][0]*s:.2f} {y:.2f}) scale({s:.5f})"><path fill="{color}" d="{W["d"]}"/></g>', (W["bounds"][2]-W["bounds"][0])*s
def lockup_svg(mark_body, mark_cres, word, bg=None):
    mh = 120; mw = mh * MW / MH; xh = 0.40 * mh; gap = 0.30 * mh
    wg, ww = wordmark_g(word, mw + gap, mh * 0.80, xh)
    tw = mw + gap + ww; pad = 0
    inner = mark_svg(mark_body, mark_cres, attrs=f'x="0" y="0" width="{mw:.2f}" height="{mh}"')
    bgr = f'<rect width="100%" height="100%" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {tw:.1f} {mh}">{bgr}{inner}{wg}</svg>'
def w(path, s): open(f"{D}/{path}", "w").write(s)
w("logo.svg", mark_svg())
w("logo-mono.svg", mono_svg())
w("logo-listening.svg", mark_svg(glow=True))
w("logo-on-paper.svg", mark_svg(pad=60).replace('viewBox', f'style="background:{C["paper"]}" viewBox').replace('<path', f'<rect x="{X0-60}" y="{Y0-60}" width="{MW+120}" height="{MH+120}" fill="{C["paper"]}"/><path', 1))
w("logo-on-forest-deep.svg", mark_svg(**DARK, pad=60).replace('<path', f'<rect x="{X0-60}" y="{Y0-60}" width="{MW+120}" height="{MH+120}" fill="{C["forest_deep"]}"/><path', 1))
w("lockup-light.svg", lockup_svg(C["forest"], C["crescent"], C["forest"]))
w("lockup-dark.svg", lockup_svg(DARK["body"], DARK["cres"], C["beige"]))
wg, ww = wordmark_g("currentColor", 0, W["xh"]*0+0, 1)
w("wordmark.svg", f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{W["bounds"][0]:.0f} {W["bounds"][1]-20:.0f} {W["bounds"][2]-W["bounds"][0]:.0f} {W["bounds"][3]-W["bounds"][1]+40:.0f}"><path fill="currentColor" d="{W["d"]}"/></svg>')
# app icon: paper rounded square, mark centered
def icon_svg(size=512, rounded=True, bg=C["paper"]):
    r = size * 0.22 if rounded else 0; mh = size * 0.66; mw = mh * MW / MH
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}"><rect width="{size}" height="{size}" rx="{r}" fill="{bg}"/>'
            + mark_svg(attrs=f'x="{(size-mw)/2:.1f}" y="{(size-mh)/2:.1f}" width="{mw:.1f}" height="{mh:.1f}"') + '</svg>')
w("icon.svg", icon_svg()); w("icon-fullbleed.svg", icon_svg(rounded=False))
w("favicon.svg", mark_svg(pad=24))
STATES = [
 ("LISTENING", "Listening", C["forest"], C["sage"], C["beige"], C["sage"], "circle", "Room 304 · English", "“…so the midterm covers ch…", True),
 ("ALERT", "Heard your name", C["paper"], C["alert"], C["forest_deep"], C["alert_ink"], "diamond", "Room 304 · alert", "“Fathi, can you answer number…", False),
 ("CATCH_UP", "Catch me up", C["forest_deep"], C["fern"], C["beige"], C["fern"], "play", "Last 5 min · summary", "2 lines · speaking", False),
 ("MUTED", "Muted", C["moss"], C["beige"], C["beige"], C["beige"], "pause", "Mic off · nothing heard", "Press pause to listen", False),
 ("OFFLINE", "Offline · all local", C["beige"], C["sage"], C["forest_deep"], C["forest"], "square", "0 bytes sent", "Wi-Fi off · still listening", False),
]
SH = dict(circle='<circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="8" cy="8" r="2.5"/>',
          diamond='<path d="M8 1 L15 8 L8 15 L1 8Z"/>', play='<path d="M3 1.5 L14 8 L3 14.5Z"/>',
          pause='<rect x="3" y="2" width="3.5" height="12"/><rect x="9.5" y="2" width="3.5" height="12"/>',
          square='<rect x="2" y="2" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"/>')
FONTS = '''@font-face{font-family:"Host Grotesk";src:url(FONTDIR/HostGrotesk-VariableFont_wght.ttf);font-weight:300 800}
@font-face{font-family:"Fragment Mono";src:url(FONTDIR/FragmentMono-Regular.ttf)}'''
def fonts(rel): return FONTS.replace("FONTDIR", rel)
def tile_html(i, st, rel="../fonts"):
    key, word, base, band, ink, label, shape, sub, foot, glow = st
    dark = base in (C["forest"], C["forest_deep"], C["moss"])
    mk = mark_svg(**(DARK if dark else {}), glow=glow, attrs='class="mark"')
    return f'''<html><head><meta charset="utf-8"><style>{fonts(rel)}
*{{margin:0;box-sizing:border-box}}body{{width:512px;height:512px;background:{base};color:{ink};position:relative;overflow:hidden;font-family:"Host Grotesk"}}
.row{{position:absolute;left:44px;right:44px;display:flex;justify-content:space-between;align-items:center;font-family:"Fragment Mono"}}
.top{{top:34px;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:{C["forest_deep"]}}} .top span{{opacity:.78}}
.bot{{bottom:42px;font-size:14px}} .bot .t{{opacity:.55}}
.rule{{position:absolute;left:44px;right:44px;height:1px;background:{ink};opacity:.22;bottom:80px}}
.mark{{position:absolute;left:{256-0.632*95:.1f}px;top:112px;height:190px}}
.state{{position:absolute;left:0;right:0;top:326px;display:flex;justify-content:center;align-items:center;gap:12px;font-family:"Fragment Mono";font-size:21px;letter-spacing:.16em;text-transform:uppercase;color:{label}}}
.state svg{{width:15px;height:15px;fill:currentColor}}
.sub{{position:absolute;left:0;right:0;top:366px;text-align:center;font-size:14px;opacity:.62}}
</style></head><body>
<div style="position:absolute;left:0;top:0;width:512px;height:80px;background:{band}"></div>
<svg width="512" height="512" style="position:absolute;inset:0" fill="none"><g stroke="{C["forest_deep"]}" stroke-opacity=".45"><path d="M24 40V24H40"/><path d="M488 40V24H472"/></g><g stroke="{ink}" stroke-opacity=".38"><path d="M24 472V488H40"/><path d="M488 472V488H472"/></g></svg>
<div class="row top"><span>{NAME}</span><span>No. 0{i+1} — now playing</span></div>
{mk}
<div class="state"><svg viewBox="0 0 16 16">{SH[shape]}</svg><span>{word}</span></div>
<div class="sub">{sub}</div><div class="rule"></div>
<div class="row bot"><span>{foot}</span><span class="t">09:4{i}</span></div></body></html>'''
os.makedirs(f"{D}/tiles", exist_ok=True)
for i, st in enumerate(STATES):
    w(f"tiles/{st[0].lower().replace('_','-')}.html", tile_html(i, st))
json.dump(dict(STATES=[s[:7] for s in STATES]), open("states.json", "w"))
tokens = json.load(open("../nowagent-docs/design/tokens.json"))
tokens["name"] = "Editorial Forest v3 · Earshot"
tokens["brand"] = {"name": NAME, "displayName": NAME_CAP, "note": "Working name. Every UI string, tile, wordmark and title reads brand.name; rerun design/_src/build.py with BRAND_NAME=kinig to rebrand."}
tokens["color"].update({"crescent": C["crescent"], "listen-glow": C["glow"]})
tokens["state"] = {s[0]: {"base": s[2], "band": s[3], "ink": s[4], "label": s[5], "shape": s[6], "word": s[1].upper()} for s in STATES}
tokens["logo"] = {"file": "logo.svg", "viewBox": f"{X0} {Y0} {MW} {MH}", "colors": {"body": "forest", "crescent": "crescent", "hollow": "transparent"},
  "onDark": {"body": "paper", "crescent": "crescent"}, "listeningGlow": "listen-glow, blurred, optional, LISTENING state only",
  "clearSpace": "0.25 × mark height", "minMarkPx": 16, "minLockupPx": 96}
json.dump(tokens, open(f"{D}/tokens.json", "w"), indent=2, ensure_ascii=False)
print("ok")
