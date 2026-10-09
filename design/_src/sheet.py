import json,os
exec(open('build.py').read().split("def w(path")[0])  # reuse C, mark_svg, lockup etc
DARKM=dict(body=C["paper"],cres=C["crescent"])
D="../earshot-docs/design"
FONT=f'''@font-face{{font-family:"Host Grotesk";src:url(fonts/HostGrotesk-VariableFont_wght.ttf);font-weight:300 800}}
@font-face{{font-family:"Fragment Mono";src:url(fonts/FragmentMono-Regular.ttf)}}'''
sw=[("forest","Forest",C["forest"],"Primary · mark body","#DDE3D3"),("forest-deep","Forest Deep",C["forest_deep"],"Darkest · ink","#DDE3D3"),
("moss","Moss",C["moss"],"Hover · muted","#DDE3D3"),("sage","Sage",C["sage"],"Secondary on dark","#12241A"),
("crescent","Crescent",C["crescent"],"Mark inner curl","#12241A"),("beige","Beige",C["beige"],"Light surface","#12241A"),("paper","Paper",C["paper"],"Lightest surface","#12241A")]
swh="".join(f'<div class="sw" style="background:{c};color:{t}"><div class="k">{k}</div><div><b>{n}</b><div class="m">{c.upper()}<br>{d}</div></div></div>' for k,n,c,d,t in sw)
acc=[("alert","Alert",C["alert"],C["alert_ink"],"diamond"),("fern","Catch-up",C["fern"],C["fern_ink"],"play"),("clay","Mic error",C["clay"],C["clay_ink"],"square"),("listen-glow","Listening",C["glow"],"#2E5E80","circle")]
SH=dict(circle='<circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="8" cy="8" r="2.5"/>',diamond='<path d="M8 1 L15 8 L8 15 L1 8Z"/>',play='<path d="M3 1.5 L14 8 L3 14.5Z"/>',square='<rect x="2" y="2" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2"/>')
acch="".join(f'<div class="acc"><div class="ah"><span style="color:{ink}"><svg viewBox="0 0 16 16" width="10" height="10" fill="currentColor">{SH[s]}</svg> {k}</span><i style="background:{c}"></i></div><b>{n}</b><div class="m">{c.upper()}<br>band, dot or glow</div></div>' for k,n,c,ink,s in acc)
tiles="".join(f'<img src="tiles/{t}.png">' for t in ["listening","alert","catch-up","muted","offline"])
html=f'''<html><head><meta charset="utf-8"><style>{FONT}
*{{margin:0;box-sizing:border-box}}body{{width:1024px;height:640px;background:{C["paper"]};color:{C["forest_deep"]};font-family:"Host Grotesk";position:relative;overflow:hidden}}
.mono,.k,.m,.hd,.lab{{font-family:"Fragment Mono"}}
.hd{{position:absolute;left:36px;right:36px;top:22px;display:flex;justify-content:space-between;font-size:8.5px;letter-spacing:.14em;text-transform:uppercase}}
.hd .l{{display:flex;gap:10px;align-items:center}}
.hr{{position:absolute;left:36px;right:36px;height:1px;background:{C["forest_deep"]};opacity:.14}}
.lab{{position:absolute;font-size:7.5px;letter-spacing:.14em;text-transform:uppercase;color:{C["ink_muted"]}}}
.hero{{position:absolute;left:36px;top:64px;width:388px;height:250px;background:{C["forest"]};color:{C["beige"]}}}
.hero .t{{position:absolute;left:24px;bottom:22px;font-size:20px;font-weight:600;letter-spacing:-.02em}} .hero .t span{{color:{C["sage"]}}}
.hero .n{{position:absolute;right:24px;bottom:24px;text-align:right;font-family:"Fragment Mono";font-size:7.5px;line-height:1.7;color:{C["sage"]}}}
.hero .c{{position:absolute;font-family:"Fragment Mono";font-size:7px;letter-spacing:.14em;color:{C["sage"]};top:26px}}
.hero svg.mk{{position:absolute;left:150px;top:44px;height:150px}}
h1{{position:absolute;left:440px;top:84px;font-size:44px;line-height:1.02;letter-spacing:-.035em;font-weight:600}} h1 span{{color:{C["ink_muted"]}}}
.intro{{position:absolute;left:440px;top:148px;width:430px;font-size:11.5px;line-height:1.45;color:{C["ink_muted"]}}}
.lk{{position:absolute;top:212px;width:268px;height:82px;display:flex;align-items:center;justify-content:center}}
.lk img{{height:34px}}
.cap{{position:absolute;top:299px;font-family:"Fragment Mono";font-size:7px;color:{C["ink_muted"]};width:268px;display:flex;justify-content:space-between}}
.sws{{position:absolute;left:36px;top:352px;display:flex}}
.sw{{width:84px;height:80px;padding:8px 8px;display:flex;flex-direction:column;justify-content:space-between}}
.sw .k{{font-size:7px;opacity:.75}} .sw b{{font-size:10px;font-weight:500}} .sw .m{{font-size:6.5px;line-height:1.5;opacity:.8}}
.accs{{position:absolute;left:640px;top:352px;display:grid;grid-template-columns:repeat(4,87px);border:1px solid rgba(18,36,26,.14)}}
.acc{{height:80px;padding:8px;border-right:1px solid rgba(18,36,26,.14)}} .acc:last-child{{border:0}}
.ah{{display:flex;justify-content:space-between;align-items:center;font-family:"Fragment Mono";font-size:6.5px}} .ah i{{width:11px;height:8px;display:block}}
.acc b{{display:block;margin-top:14px;font-size:9.5px;font-weight:500}} .acc .m{{font-size:6.5px;color:{C["ink_muted"]};margin-top:4px;line-height:1.5}}
.ty{{position:absolute;left:36px;top:474px}} .ty .aa{{font-size:28px;font-weight:600;letter-spacing:-.02em}}
.ty .aa2{{font-size:20px;margin-top:4px}} .ty .aa2 span{{margin-right:6px}}
.tyd{{position:absolute;left:130px;top:478px;font-size:9.5px;line-height:1.5;width:200px}} .tyd .m{{font-family:"Fragment Mono";font-size:7px;color:{C["ink_muted"]}}}
.code{{display:inline-block;margin-top:8px;background:{C["forest"]};color:{C["beige"]};font-family:"Fragment Mono";font-size:8px;padding:4px 7px}}
.cs{{position:absolute;left:372px;top:478px;width:110px;height:120px;border:1px dashed rgba(18,36,26,.3);display:flex;align-items:center;justify-content:center}}
.cs img{{height:72px}}
.csn{{position:absolute;left:494px;top:520px;font-family:"Fragment Mono";font-size:7px;line-height:1.7;color:{C["ink_muted"]}}}
.tl{{position:absolute;left:640px;top:478px;display:grid;grid-template-columns:repeat(5,64px);gap:8px}} .tl img{{width:64px;height:64px}}
.tln{{position:absolute;left:640px;top:552px;width:350px;font-family:"Fragment Mono";font-size:7px;line-height:1.7;color:{C["ink_muted"]}}}
</style></head><body>
<div class="hd"><div class="l">{mark_svg(attrs='height="12"')}<span>{NAME} &nbsp;/&nbsp; brand identity</span></div><span>Editorial Forest — v3</span><span>AppBuilders PH 2026 · Oct 2026</span></div>
<div class="hr" style="top:46px"></div>
<div class="hero"><span class="c" style="left:24px">01 — THE MARK</span><span class="c" style="right:24px">2 COLOURS · HOLLOW = BACKGROUND</span>
{mark_svg(**DARKM,glow=True,attrs='class="mk"')}
<div class="t">An ear, <span>listening.</span></div><div class="n">Forest body · crescent curl.<br>Blue glow = listening only.</div></div>
<span class="lab" style="left:440px;top:64px">02 — Voice</span>
<h1>Hear what matters. <span>Offline.</span></h1>
<div class="intro">A private companion that listens to your day on your laptop and puts it on the screens you already own: live captions, your name, a 2-line catch-up. Calm, editorial, unhurried. Nothing leaves the laptop.</div>
<div class="lk" style="left:440px;background:{C["beige"]}"><img src="lockup-light.svg"></div>
<div class="lk" style="left:722px;background:{C["forest_deep"]}"><img src="lockup-dark.svg"></div>
<div class="cap" style="left:440px"><span>Lockup — light</span><span>forest + crescent on beige / paper</span></div>
<div class="cap" style="left:722px"><span>Lockup — dark</span><span>paper + crescent on forest-deep</span></div>
<div class="hr" style="top:326px"></div>
<span class="lab" style="left:36px;top:337px">03 — Colour</span><span class="lab" style="left:640px;top:337px">State accents · never fills</span>
<div class="sws">{swh}</div><div class="accs">{acch}</div>
<div class="hr" style="top:448px"></div>
<span class="lab" style="left:36px;top:459px">04 — Type</span><span class="lab" style="left:372px;top:459px">05 — Clear space &amp; size</span><span class="lab" style="left:640px;top:459px">06 — Now playing art</span>
<div class="ty"><div class="aa">Aa</div><div class="aa2"><span style="font-weight:400">Aa</span><span style="font-weight:500">Aa</span><span style="font-weight:600">Aa</span></div><div class="mono" style="font-size:18px;margin-top:6px">{{ }}</div></div>
<div class="tyd"><b style="font-weight:600">Host Grotesk</b><div class="m">One family for display + UI · 600 at display sizes</div><br><b style="font-weight:500">400 / 500 / 600</b><div class="m">Body 17 · captions 600 · emphasis by weight + tone</div><div class="code">“…covers chapters four to six.”</div><div class="m" style="margin-top:4px">Fragment Mono · timestamps, metadata</div></div>
<div class="cs"><img src="logo.svg"></div><div class="csn">x = ¼ mark height<br>min 16 px · lockup 96 px<br>wordmark {NAME}<br>Host Grotesk 500<br>name = tokens.brand.name</div>
<div class="tl">{tiles}</div><div class="tln">Listening · Alert · Catch-up · Muted · Offline. Title = the caption line,<br>artist = the line before it. Every state = colour + shape + word.</div>
</body></html>'''
open(f"{D}/brand-sheet.html","w").write(html)
