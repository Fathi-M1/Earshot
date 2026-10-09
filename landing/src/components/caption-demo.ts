import { useEffect, useState } from "react";
import { usePrefersReducedMotion } from "@/components/use-reduced-motion";

export const alertLine = "Fathi, quiz moved to Monday";

const lines = [
  {
    words: ["The", "quiz", "covers", "chapters", "four", "to", "six."],
    gloss: "",
    dir: "ltr" as const,
  },
  {
    words: ["Ang", "quiz", "ay", "sakop", "ang", "chapters", "four", "hanggang", "six."],
    gloss: "The quiz covers chapters four to six.",
    dir: "ltr" as const,
  },
  {
    words: ["انتقل", "الاختبار", "إلى", "يوم", "الاثنين."],
    gloss: "The quiz moved to Monday.",
    dir: "rtl" as const,
  },
];

export type CaptionDemo = {
  previous: string;
  current: string;
  gloss: string;
  dir: "ltr" | "rtl";
  alert: boolean;
  cycle: number;
};

const settled: CaptionDemo = {
  previous: lines[1].words.join(" "),
  current: lines[2].words.join(" "),
  gloss: lines[2].gloss,
  dir: "rtl",
  alert: true,
  cycle: 0,
};

const empty: CaptionDemo = {
  previous: "",
  current: "",
  gloss: "",
  dir: "ltr",
  alert: false,
  cycle: 0,
};

export function useCaptionDemo(active: boolean) {
  const reduced = usePrefersReducedMotion();
  const [demo, setDemo] = useState<CaptionDemo>(reduced ? settled : empty);

  useEffect(() => {
    if (reduced) {
      setDemo(settled);
      return;
    }
    if (!active) return;

    let cancelled = false;
    const timers: number[] = [];
    const wait = (ms: number) =>
      new Promise<void>((resolve) => {
        timers.push(window.setTimeout(resolve, ms));
      });

    const run = async () => {
      let cycle = 0;
      while (!cancelled) {
        setDemo({ ...empty, cycle });
        await wait(360);
        for (let index = 0; index < lines.length; index += 1) {
          const line = lines[index];
          const previous = index === 0 ? "" : lines[index - 1].words.join(" ");
          for (let count = 1; count <= line.words.length; count += 1) {
            if (cancelled) return;
            setDemo({
              previous,
              current: line.words.slice(0, count).join(" "),
              gloss: count === line.words.length ? line.gloss : "",
              dir: line.dir,
              alert: false,
              cycle,
            });
            await wait(160);
          }
          await wait(640);
        }
        if (cancelled) return;
        setDemo((current) => ({ ...current, alert: true }));
        await wait(3400);
        cycle += 1;
      }
    };

    void run();
    return () => {
      cancelled = true;
      timers.forEach((id) => window.clearTimeout(id));
    };
  }, [active, reduced]);

  return demo;
}
