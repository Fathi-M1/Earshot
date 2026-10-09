import { unmeasured } from "@/lib/brand";
import { Reveal } from "@/components/reveal";
import { SectionHeader } from "@/components/section-header";

const rows = [
  { label: "Microphone", value: "Listening" },
  { label: "Raw audio on disk", value: "none — RAM only, last 30 s" },
  { label: "Bytes sent to the internet", value: unmeasured },
  { label: "Internet connections", value: unmeasured },
  { label: "Internet reachable", value: unmeasured },
  { label: "Models on this machine", value: unmeasured },
];

export function Privacy() {
  return (
    <section className="section surface-dark" id="privacy">
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
        <Reveal delay={80}>
          <dl className="proof">
            {rows.map((row) => (
              <div key={row.label}>
                <dt>{row.label}</dt>
                <dd className="nums">{row.value}</dd>
              </div>
            ))}
          </dl>
          <p className="fine is-on-dark">Measured live on this laptop. Values show — until measured.</p>
        </Reveal>
      </div>
    </section>
  );
}
