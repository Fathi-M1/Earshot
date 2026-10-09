import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function SectionHeader({
  eyebrow,
  title,
  tone,
  intro,
  align = "center",
  as = "h2",
}: {
  eyebrow: string;
  title: string;
  tone?: string;
  intro: string;
  align?: "center" | "left";
  as?: "h1" | "h2";
}) {
  const Title = as;
  const titleClass = as === "h1" ? "hero-title" : "display";
  return (
    <header className={cn("section-head", align === "center" && "is-center")}>
      <p className="eyebrow">{eyebrow}</p>
      <Title className={titleClass}>
        {title}{" "}
        {tone ? <span className="tone">{tone}</span> : null}
      </Title>
      <p className="intro">{intro}</p>
    </header>
  );
}

export function Overline({ children }: { children: ReactNode }) {
  return <p className="overline">{children}</p>;
}
