import { githubUrl } from "@/lib/brand";
import { Button } from "@/components/ui/button";
import { Reveal } from "@/components/reveal";

export function Close() {
  return (
    <section className="section close" id="github">
      <div className="wrap wrap-text">
        <Reveal>
          <header className="section-head is-center">
            <p className="eyebrow">GitHub</p>
            <h2 className="display">
              The source is public. <span className="tone">The models stay put.</span>
            </h2>
            <p className="intro">
              Clone it, run it on the laptop, and cut the network. Captions, alerts, and catch-up
              do not call a cloud model.
            </p>
            <p className="hero-actions">
              <Button asChild>
                <a href={githubUrl} rel="noreferrer">
                  View on GitHub
                </a>
              </Button>
            </p>
          </header>
        </Reveal>
      </div>
    </section>
  );
}
