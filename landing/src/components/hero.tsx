import { useEffect, useRef, useState } from "react";
import { brand, sample } from "@/lib/brand";
import { Button } from "@/components/ui/button";
import { Reveal } from "@/components/reveal";
import { IPhone } from "@/components/devices";
import { NextIcon, PauseMark, PrevIcon } from "@/components/shapes";
import { TileArt } from "@/components/tile-art";

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

function LockScreen() {
  return (
    <IPhone>
      <p className="lock-date">{sample.when}</p>
      <p className="lock-time">{sample.clock}</p>
      <div className="now-playing">
        <div className="now-row">
          <TileArt name="alert" size={96} radius={14} />
          <div>
            <p className="now-title">{sample.alert}</p>
            <p className="now-artist">{sample.artist}</p>
          </div>
        </div>
        <div className="now-track" />
        <div className="now-meta">
          <span>LIVE</span>
          <span>ALERT</span>
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

function CaptionPhone() {
  return (
    <IPhone>
      <div className="phone-top">
        <i className="status-dot" />
        <span>live</span>
      </div>
      <TileArt name="listening" size={196} radius={14} />
      <p className="phone-now">{sample.current}</p>
      <p className="phone-prev">{sample.previous}</p>
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
  const stage = useStageScale(640, 528);

  return (
    <section className="section hero" id="overview">
      <div className="wrap wrap-text">
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
      <div className="hero-clip wrap wrap-hero" ref={stage.ref} style={{ height: stage.height }}>
        <div className="hero-stage" style={{ transform: `scale(${stage.scale})` }}>
          <CaptionPhone />
          <LockScreen />
        </div>
      </div>
    </section>
  );
}
