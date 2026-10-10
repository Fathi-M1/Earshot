import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useReducedMotion } from "motion/react";
import logo from "../../../design/logo.svg";
import { brand, captions, githubUrl, languages } from "@/lib/brand";
import { Marquee } from "@/components/fx/marquee";
import { PageMeta } from "@/components/page-meta";
import { Rise } from "@/components/rise";

const cycle = captions.slice(0, 3);
const codes = ["EN", "TL", "AR"] as const;

function lineDir(text: string) {
  return /[\u0600-\u06FF]/.test(text) ? "rtl" : "ltr";
}

function useLine() {
  const reduced = useReducedMotion();
  const [index, setIndex] = useState(0);
  const [count, setCount] = useState(reduced ? cycle[0].length : 0);
  const line = cycle[index];

  useEffect(() => {
    if (reduced) {
      setCount(line.length);
      return;
    }
    const step = Math.max(18, Math.floor(3200 / line.length));
    if (count < line.length) {
      const tick = window.setTimeout(() => setCount((value) => value + 1), step);
      return () => window.clearTimeout(tick);
    }
    const hold = window.setTimeout(() => {
      setIndex((value) => (value + 1) % cycle.length);
      setCount(0);
    }, 800);
    return () => window.clearTimeout(hold);
  }, [count, line, reduced]);

  const previous = cycle[(index + cycle.length - 1) % cycle.length];
  const older = cycle[(index + cycle.length - 2) % cycle.length];
  return { typed: line.slice(0, count), previous, older, dir: lineDir(line), code: codes[index] } as const;
}

function CaptionScreen({
  typed,
  previous,
  older,
  dir,
  code,
}: {
  typed: string;
  previous: string;
  older: string;
  dir: "ltr" | "rtl";
  code: string;
}) {
  return (
    <div className="caption-ui">
      <p className="caption-meta">
        <span>LISTENING · {code}</span>
        <span>0 BYTES SENT</span>
      </p>
      <div className="caption-stack">
        <p className="caption-line is-old" dir={lineDir(older)}>
          {older}
        </p>
        <p className="caption-line is-mid" dir={lineDir(previous)}>
          {previous}
        </p>
        <p className="caption-line is-new" dir={dir}>
          {typed}
        </p>
      </div>
    </div>
  );
}

function Devices({ line }: { line: ReturnType<typeof useLine> }) {
  const shown = line.typed;
  return (
    <div className="stage">
      <div className="laptop">
        <div className="laptop-lid">
          <span className="camera" />
          <div className="laptop-screen">
            <CaptionScreen {...line} />
          </div>
        </div>
        <div className="laptop-base" />
      </div>
      <div className="device-phone">
        <span className="island" />
        <p className="lock-date">Saturday, October 10</p>
        <p className="phone-time">09:41</p>
        <div className="now-playing">
          <img src={logo} alt="" width={28} height={28} />
          <p dir={line.dir}>{shown}</p>
        </div>
      </div>
      <div className="garmin">
        <span className="strap strap-top" />
        <div className="watch-ring">
          <span className="nub n1" />
          <span className="nub n2" />
          <span className="nub n3" />
          <span className="nub n4" />
          <span className="nub n5" />
          <div className="watch-face">
            <p className="mono">Earshot</p>
            <p dir={line.dir}>{shown}</p>
          </div>
        </div>
        <span className="strap strap-bottom" />
      </div>
    </div>
  );
}

const features = [
  {
    title: "Live captions",
    line: "Every line, as it's said.",
    body: (
      <>
        <p className="caption-line is-old">Boarding for flight 5J 812 now at gate 14.</p>
        <p className="caption-line is-mid">Lilipat ang meeting sa Lunes ng alas-diyes.</p>
        <p className="caption-line is-new">Fathi, can you take the next point?</p>
      </>
    ),
  },
  {
    title: "Heard your name",
    line: "The line that named you.",
    body: <p className="caption-line is-new">Fathi, can you take the next point?</p>,
  },
  {
    title: "Catch me up",
    line: "Two lines you missed.",
    body: (
      <>
        <p className="caption-line is-mid">The meeting moves to Monday at ten.</p>
        <p className="caption-line is-new">The deadline moved to Friday.</p>
      </>
    ),
  },
  {
    title: "Translate",
    line: "Read it in your language.",
    body: (
      <>
        <p className="chip">TL → EN</p>
        <p className="caption-line is-new">Lilipat ang meeting sa Lunes ng alas-diyes.</p>
      </>
    ),
  },
  {
    title: "Sessions & recall",
    line: "The quote, with the time.",
    body: <p className="caption-line is-new">“The deadline moved to Friday.” 10:42</p>,
  },
];

function Showcase() {
  const reduced = useReducedMotion();
  const [active, setActive] = useState(0);

  useEffect(() => {
    if (reduced) return;
    const id = window.setTimeout(() => setActive((value) => (value + 1) % features.length), 4000);
    return () => window.clearTimeout(id);
  }, [active, reduced]);

  const feature = features[active];
  return (
    <div className="showcase">
      <div className="feature-tabs" role="tablist">
        {features.map((item, index) => (
          <button
            key={item.title}
            type="button"
            role="tab"
            aria-selected={index === active}
            className={index === active ? "is-on" : undefined}
            onClick={() => setActive(index)}
          >
            {item.title}
          </button>
        ))}
      </div>
      <div className="feature-list" role="tablist">
        {features.map((item, index) => (
          <button
            key={item.title}
            type="button"
            role="tab"
            aria-selected={index === active}
            className={index === active ? "is-on" : undefined}
            onClick={() => setActive(index)}
          >
            <strong>{item.title}</strong>
            <span>{item.line}</span>
          </button>
        ))}
      </div>
      <div className="showcase-stage">
        <div className="device-phone showcase-phone" key={feature.title}>
          <span className="island" />
          <div className="phone-feature">{feature.body}</div>
        </div>
      </div>
    </div>
  );
}

export function Home() {
  const line = useLine();
  useEffect(() => {
    const id = window.location.hash.replace("#", "");
    if (id) document.getElementById(id)?.scrollIntoView();
  }, []);
  return (
    <>
      <PageMeta
        title={brand.displayName}
        description="Live captions and alerts on your phone and watch, powered by AI that never leaves your laptop."
      />
      <section className="section hero">
        <div className="hero-copy">
          <h1>Hear what matters. Offline.</h1>
          <p className="lede">
            Live captions and alerts on your phone and watch, powered by AI that never leaves your laptop.
          </p>
          <div className="cta-row">
            <Link className="pill" to="/#get">
              Get {brand.displayName}
            </Link>
            <Link className="text-link" to="/how-it-works">
              How it works →
            </Link>
          </div>
        </div>
        <Devices line={line} />
      </section>

      <section className="marquee-wrap" aria-label="Languages">
        <Marquee>
          {languages.map((item) => (
            <p className="lang-item" key={item.code + item.line} dir={item.dir}>
              <span>{item.code}</span>
              {item.line}
            </p>
          ))}
        </Marquee>
      </section>

      <section className="section">
        <h2>You zoned out. Your name didn't.</h2>
        <div className="split">
          <Rise>
            <h3>Said once.</h3>
            <p>Your name, a quiz, a deadline. {brand.displayName} catches it.</p>
          </Rise>
          <Rise>
            <h3>In three languages.</h3>
            <p>English, Tagalog, Arabic.</p>
          </Rise>
        </div>
      </section>

      <section className="section" id="features">
        <h2>What it does.</h2>
        <Showcase />
      </section>

      <section className="section">
        <h2>Nothing leaves the laptop.</h2>
        <dl className="status">
          <div>
            <dt>Microphone</dt>
            <dd>Listening</dd>
          </div>
          <div>
            <dt>Raw audio saved</dt>
            <dd>Never</dd>
          </div>
          <div>
            <dt>Bytes to the internet</dt>
            <dd>0</dd>
          </div>
          <div>
            <dt>Mute</dt>
            <dd>One press, every screen</dd>
          </div>
        </dl>
        <Link className="text-link" to="/privacy">
          Read the privacy policy →
        </Link>
      </section>

      <section className="section close-block" id="get">
        <img src={logo} alt="" width={40} height={64} />
        <h2>Clone it. Cut the Wi-Fi. Keep listening.</h2>
        <a className="pill" href={githubUrl} rel="noreferrer">
          View on GitHub ↗
        </a>
        <p className="mono">Windows · 8 GB RAM+ · no GPU needed</p>
      </section>
    </>
  );
}
