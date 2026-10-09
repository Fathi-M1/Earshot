import { useEffect, useRef, useState } from "react";
import { sample, unmeasured } from "@/lib/brand";
import { cn } from "@/lib/utils";
import { CaptionBar } from "@/components/devices";
import { Reveal } from "@/components/reveal";
import { SectionHeader } from "@/components/section-header";
import { Diamond, PlayMark } from "@/components/shapes";
import { TileArt } from "@/components/tile-art";
import { useDemoActive } from "@/components/use-demo";

const languages = [
  { id: "en", label: "EN", badge: "EN" },
  { id: "tl", label: "TL", badge: "TL→EN" },
  { id: "ar", label: "AR", badge: "AR→EN" },
  { id: "es", label: "ES", badge: "ES→EN" },
] as const;

function CaptionsTile() {
  const demo = useDemoActive<HTMLElement>(0.4);
  return (
    <Reveal className="tile span-7" delay={0}>
      <article ref={demo.ref} onMouseEnter={demo.onMouseEnter} onMouseLeave={demo.onMouseLeave}>
        <div className="tile-kicker">
          <h3 className="headline">Live captions.</h3>
          <div className={cn("wave", demo.active && "is-on")} aria-hidden="true">
            <i />
            <i />
            <i />
            <i />
            <i />
          </div>
        </div>
        <p className="tile-copy">
          Partials stay on the laptop bar. Committed lines go to the lock screen, one update at a
          time.
        </p>
        <ul className="transcript">
          <li>
            <span className="nums">{sample.clock}</span>
            <span>{sample.previous}</span>
          </li>
          <li>
            <span className="nums">{sample.clock}</span>
            <span>{sample.current}</span>
          </li>
        </ul>
        <div className="tile-bleed">
          <CaptionBar mode="listening" />
        </div>
      </article>
    </Reveal>
  );
}

function AlertsTile() {
  const demo = useDemoActive<HTMLElement>(0.4);
  return (
    <Reveal className="tile span-5" delay={60}>
      <article
        className="tile-alert"
        ref={demo.ref}
        onMouseEnter={demo.onMouseEnter}
        onMouseLeave={demo.onMouseLeave}
      >
        <h3 className="headline">Heard your name.</h3>
        <p className="tile-copy">Your name, a deadline, a gate. The matching line becomes the track.</p>
        <p className="state-label is-needs">
          <span className={cn("pulse-dot", demo.active && "is-on")} aria-hidden="true" />
          <Diamond size={12} /> Heard your name
        </p>
        <div className="tile-bleed is-art">
          <TileArt name="alert" size={220} radius={14} />
        </div>
      </article>
    </Reveal>
  );
}

function CatchUpTile() {
  const demo = useDemoActive<HTMLElement>(0.4);
  return (
    <Reveal className="tile span-4" delay={120}>
      <article ref={demo.ref} onMouseEnter={demo.onMouseEnter} onMouseLeave={demo.onMouseLeave}>
        <h3 className="headline">Catch me up.</h3>
        <p className="tile-copy">
          Previous asks for two short lines from the last few minutes, then speaks them in your
          earbuds.
        </p>
        <div className={cn("recap", demo.active && "is-on")} key={demo.active ? "on" : "off"}>
          <p className="state-label is-approved">
            <PlayMark size={12} /> Catch me up
          </p>
          <p className="recap-line">{sample.catch1}</p>
          <p className="recap-line">{sample.catch2}</p>
        </div>
      </article>
    </Reveal>
  );
}

function MuteTile() {
  const demo = useDemoActive<HTMLElement>(0.35);
  const [muted, setMuted] = useState(false);
  const held = useRef(false);

  useEffect(() => {
    if (!demo.active || held.current) return;
    const kick = window.setTimeout(() => {
      if (!held.current) setMuted(true);
    }, 900);
    const id = window.setInterval(() => {
      if (!held.current) setMuted((value) => !value);
    }, 2800);
    return () => {
      window.clearTimeout(kick);
      window.clearInterval(id);
    };
  }, [demo.active]);

  return (
    <Reveal className="tile span-12" delay={180}>
      <article ref={demo.ref} onMouseEnter={demo.onMouseEnter} onMouseLeave={demo.onMouseLeave}>
        <div className="mute-copy">
          <h3 className="headline">Privacy mute.</h3>
          <p className="tile-copy">One press closes the microphone. Every surface says muted.</p>
          <button
            type="button"
            className="text-button"
            onClick={() => {
              held.current = true;
              setMuted((value) => !value);
            }}
          >
            {muted ? "Listen" : "Mute"}
          </button>
        </div>
        <CaptionBar mode={muted ? "muted" : "listening"} />
      </article>
    </Reveal>
  );
}

export function Bento() {
  const [language, setLanguage] = useState<(typeof languages)[number]["id"]>("tl");
  const active = languages.find((item) => item.id === language) ?? languages[1];

  return (
    <section className="section band-beige" id="capabilities">
      <div className="wrap wrap-wide">
        <Reveal>
          <div className="wrap wrap-text flush">
            <SectionHeader
              eyebrow="Capabilities"
              title="Six jobs."
              tone="No new app."
              intro="Captions, your name, a two-line catch-up, a translation, the exact quote, and mute. On the screens you already own."
            />
          </div>
        </Reveal>
        <div className="bento">
          <CaptionsTile />
          <AlertsTile />
          <CatchUpTile />
          <Reveal className="tile span-4" delay={180}>
            <article>
              <h3 className="headline">Translate.</h3>
              <p className="tile-copy">
                English, Tagalog, Arabic, and Spanish. The badge shows the direction. Accuracy on
                this page is {unmeasured}.
              </p>
              <div className="segmented" role="tablist" aria-label="Caption language">
                {languages.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    role="tab"
                    aria-selected={language === item.id}
                    className={language === item.id ? "is-on" : undefined}
                    onClick={() => setLanguage(item.id)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
              <p className="lang-badge">{active.badge}</p>
            </article>
          </Reveal>

          <Reveal className="tile span-4" delay={180}>
            <article>
              <h3 className="headline">Recall.</h3>
              <p className="tile-copy">
                Ask what was said. The answer keeps an exact quote, or it says the line was not
                found.
              </p>
              <blockquote className="quote">“{sample.quote}”</blockquote>
              <p className="quote-meta nums">
                {unmeasured} · Room 304
              </p>
            </article>
          </Reveal>

          <MuteTile />
        </div>
      </div>
    </section>
  );
}
