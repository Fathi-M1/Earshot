import { useReducedMotion } from "motion/react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Marquee({
  children,
  reverse = false,
  className,
}: {
  children: ReactNode;
  reverse?: boolean;
  className?: string;
}) {
  const reduced = useReducedMotion();
  return (
    <div className={cn("marquee", reverse && "is-reverse", reduced && "is-static", className)}>
      <div className="marquee-track">
        <div className="marquee-group">{children}</div>
        <div className="marquee-group" aria-hidden="true">
          {children}
        </div>
      </div>
    </div>
  );
}
