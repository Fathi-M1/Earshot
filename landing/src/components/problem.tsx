import { Reveal } from "@/components/reveal";
import { SectionHeader } from "@/components/section-header";

const problems = [
  {
    index: "01",
    title: "Missed announcements.",
    body: "A name, a quiz date, a deadline, a gate change. Said once, out loud, while you were somewhere else in the room.",
  },
  {
    index: "02",
    title: "Another language.",
    body: "The room moves between English, Tagalog, Arabic, and Spanish. You should still be able to read the line.",
  },
  {
    index: "03",
    title: "Other people’s voices.",
    body: "That audio is not yours to upload. It stays on the laptop. The cloud is not in the path.",
  },
];

export function Problem() {
  return (
    <section className="section band-beige" id="problem">
      <div className="wrap wrap-wide">
        <Reveal>
          <div className="wrap wrap-text flush">
            <SectionHeader
              eyebrow="The problem"
              title="You zoned out."
              tone="Your name didn’t."
              intro="The quiz date, the deadline, the gate change. Said once, out loud, while you weren’t listening."
            />
          </div>
        </Reveal>
        <div className="problem-grid">
          {problems.map((item, index) => (
            <Reveal key={item.index} delay={index * 80} className="problem-item">
              <p className="overline">{item.index}</p>
              <h3 className="title">{item.title}</h3>
              <p className="body">{item.body}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
