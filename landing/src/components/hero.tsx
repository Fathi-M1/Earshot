import { useEffect, useRef, useState } from "react";
import { brand, sample } from "@/lib/brand";
import { Button } from "@/components/ui/button";
import { Reveal } from "@/components/reveal";
import { IPhone, WatchFace } from "@/components/devices";
import { ListeningField } from "@/components/listening-field";
import { alertLine, useCaptionDemo, type CaptionDemo } from "@/components/caption-demo";
import { Diamond, NextIcon, PauseMark, PrevIcon } from "@/components/shapes";
import { TileArt } from "@/components/tile-art";
import { useInView } from "@/components/use-demo";

function useStageScale(naturalWidth: number, naturalHeight: number) {
  const ref = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const measure = () => {
      const next = Math.min(1, node.clientWidth / naturalWidth);
      setScale(next > 0 ? next : 1);
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(node);
    return () => observer.disconnect();
  }, [naturalWidth]);

  return { ref, scale, height: naturalHeight * scale };
}

function LockScreen({ demo }: { demo: CaptionDemo }) {
  const title = demo.alert ? alertLine : demo.previous || "Listening";
  const artist = demo.alert ? "Quiz" : brand.displayName;
  return (
    <IPhone>
      <p className="lock-date">{sample.when}</p>
      <p className="lock-time">{sample.clock}</p>
      <WatchFace
        className={demo.alert ? "is-mini slide-in" : "is-mini"}
        title={title}
        artist={artist}
        alert={demo.alert}
        key={`watch-${demo.cycle}-${demo.alert}`}
      />
      <div
        className={demo.alert ? "now-playing is-alert slide-in" : "now-playing"}
        key={`card-${demo.cycle}-${demo.alert}`}
      >
        <div className="now-row">
          <TileArt name={demo.alert ? "alert" : "listening"} size={72} radius={14} />
          <div>
            <p className="now-title">
              {demo.alert ? <Diamond size={11} /> : null}
              {title}
            </p>
            <p className="now-artist">{artist}</p>
          </div>
        </div>
        <div className="now-track" />
        <div className="now-meta">
          <span>{demo.alert ? "ALERT" : "LIVE"}</span>
          <span>{demo.alert ? "QUIZ" : "EN"}</span>
        </div>
        <div className="now-controls">
          <PrevIcon />
          <PauseMark size={22} />
          <NextIcon />
        </div>
      </div>
    </IPhone>
  );
}

function CaptionPhone({ demo }: { demo: CaptionDemo }) {
  return (
    <IPhone>
      <div className="phone-top">
        <i className="status-dot" />
        <span>live</span>
      </div>
      <TileArt name="listening" size={132} radius={14} />
      <div className="live-captions">
        <p className="phone-prev">{demo.previous || " "}</p>
        <p className="phone-now" dir={demo.dir}>
          {demo.current || " "}
        </p>
        <p className="phone-gloss">{demo.gloss || " "}</p>
      </div>
      <p className="phone-state">LISTENING · {sample.clock}</p>
      <div className="phone-controls">
        <span>
          <PrevIcon />
          Catch me up
        </span>
        <span className="is-moss">
          <PauseMark size={18} />
          Mute
        </span>
        <span className="is-paper">
          <NextIcon />
          Bookmark
        </span>
      </div>
    </IPhone>
  );
}

export function Hero() {
  const stage = useStageScale(640, 520);
  const [stageRef, stageVisible] = useInView<HTMLDivElement>(0.15);
  const demo = useCaptionDemo(stageVisible);

  return (
    <section className="section hero" id="overview">
      <ListeningField />
      <div className="wrap wrap-text hero-copy">
        <Reveal>
          <header className="section-head is-center">
            <p className="eyebrow">{brand.displayName}</p>
            <h1 className="hero-title">
              Hear what matters. <span className="tone">Offline.</span>
            </h1>
            <p className="intro">
              A private companion that listens on your laptop and puts captions, your name and a
              quick catch-up on the screens you already own.
            </p>
            <p className="hero-actions">
              <Button variant="link" size="inline" asChild>
                <a href="#how">See how it works ›</a>
              </Button>
            </p>
            <p className="fine">Illustrative screens. Sample lines, not a measured transcript.</p>
          </header>
        </Reveal>
      </div>
      <div
        className="hero-clip wrap wrap-hero"
        ref={(node) => {
          stage.ref.current = node;
          stageRef.current = node;
        }}
        style={{ height: stage.height }}
      >
        <div className="hero-stage" style={{ transform: `scale(${stage.scale})` }}>
          <CaptionPhone demo={demo} />
          <LockScreen demo={demo} />
        </div>
      </div>
    </section>
  );
}
