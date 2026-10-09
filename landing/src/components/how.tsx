import { sample } from "@/lib/brand";
import { CaptionBar, WatchFace } from "@/components/devices";
import { Reveal } from "@/components/reveal";
import { SectionHeader } from "@/components/section-header";
import { Diamond } from "@/components/shapes";
import { TileArt } from "@/components/tile-art";

const steps = [
  {
    index: "01",
    title: "It listens on your laptop.",
    body: "Speech becomes caption lines on a bar along the bottom of the screen. The microphone never writes a file.",
  },
  {
    index: "02",
    title: "It catches your name.",
    body: "A keyword, a fuzzy match, a phonetic check. The line that named you stays in view.",
  },
  {
    index: "03",
    title: "Your watch tells you.",
    body: "The lock screen is a Now Playing track. A Garmin mirrors the title and the artist. The watch does not vibrate.",
  },
];

export function How() {
  return (
    <section className="section" id="how">
      <div className="wrap wrap-wide">
        <Reveal>
          <div className="wrap wrap-text flush">
            <SectionHeader
              eyebrow="How it works"
              title="It listens."
              tone="Your watch shows it."
              intro="Speech is transcribed on the laptop. Each line becomes the Now Playing track."
            />
          </div>
        </Reveal>
        <div className="how-grid">
          <Reveal delay={0}>
            <article className="how-step">
              <div className="how-visual">
                <CaptionBar mode="listening" />
              </div>
              <p className="overline">{steps[0].index}</p>
              <h3 className="title">{steps[0].title}</h3>
              <p className="body">{steps[0].body}</p>
            </article>
          </Reveal>
          <Reveal delay={80}>
            <article className="how-step">
              <div className="how-visual how-alert">
                <TileArt name="alert" size={148} radius={14} />
                <div>
                  <p className="how-kicker">
                    <Diamond size={12} /> Heard your name
                  </p>
                  <p className="how-line">{sample.alert}</p>
                  <p className="how-artist">{sample.artist}</p>
                </div>
              </div>
              <p className="overline">{steps[1].index}</p>
              <h3 className="title">{steps[1].title}</h3>
              <p className="body">{steps[1].body}</p>
            </article>
          </Reveal>
          <Reveal delay={160}>
            <article className="how-step">
              <div className="how-visual is-watch">
                <WatchFace title={sample.alert} artist={sample.artist} />
              </div>
              <p className="overline">{steps[2].index}</p>
              <h3 className="title">{steps[2].title}</h3>
              <p className="body">{steps[2].body}</p>
            </article>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
