import { useEffect, useRef, useState } from "react";
import { unmeasured } from "@/lib/brand";
import { Reveal } from "@/components/reveal";
import { SectionHeader } from "@/components/section-header";
import { usePrefersReducedMotion } from "@/components/use-reduced-motion";
import { useInView } from "@/components/use-demo";

const rows = [
  { label: "Microphone", value: "Listening" },
  { label: "Raw audio on disk", value: "none — RAM only, last 30 s" },
  { label: "Bytes sent to the internet", value: "" },
  { label: "Internet connections", value: unmeasured },
  { label: "Internet reachable", value: unmeasured },
  { label: "Models on this machine", value: unmeasured },
];

export function Privacy() {
  const reduced = usePrefersReducedMotion();
  const [sectionRef, inView] = useInView<HTMLElement>(0.3);
  const [cut, setCut] = useState(false);
  const played = useRef(false);
  const timer = useRef(0);
  const bytes = cut ? "0 bytes sent" : unmeasured;

  useEffect(() => {
    if (reduced || !inView || played.current) return;
    timer.current = window.setTimeout(() => {
      played.current = true;
      setCut(true);
    }, 700);
    return () => window.clearTimeout(timer.current);
  }, [inView, reduced]);

  return (
    <section className="section surface-dark" id="privacy" ref={sectionRef}>
      <div className="wrap wrap-wide">
        <Reveal>
          <div className="wrap wrap-text flush">
            <SectionHeader
              eyebrow="Privacy"
              title="Nothing leaves"
              tone="the laptop."
              intro="Runs on a 16 GB laptop. Zero bytes to the cloud. Speech recognition, alerts and summaries stay here. Audio lives in memory for 30 seconds and is gone. Only text is kept, and it expires."
            />
          </div>
        </Reveal>
        <Reveal delay={60}>
          <div className="cut-row">
            <div className="cut-copy">
              <strong>{cut ? "Internet cut" : "Internet on"}</strong>
              <span className="byte-readout">{bytes}</span>
            </div>
            <button
              type="button"
              className={cut ? "cut-switch is-cut" : "cut-switch"}
              role="switch"
              aria-checked={cut}
              aria-label={cut ? "Restore internet" : "Cut internet"}
              onClick={() => {
                played.current = true;
                window.clearTimeout(timer.current);
                setCut((value) => !value);
              }}
            >
              <i />
            </button>
          </div>
          <dl className="proof">
            {rows.map((row) => (
              <div key={row.label}>
                <dt>{row.label}</dt>
                <dd className="nums">{row.label.startsWith("Bytes") ? bytes : row.value}</dd>
              </div>
            ))}
          </dl>
          <p className="fine is-on-dark">
            The counter stays at 0 while the cut is on. Other values show — until measured on this
            laptop.
          </p>
        </Reveal>
      </div>
    </section>
  );
}
