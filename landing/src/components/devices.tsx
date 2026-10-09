import type { ReactNode } from "react";
import { sample } from "@/lib/brand";
import { cn } from "@/lib/utils";
import { Diamond, PauseMark } from "@/components/shapes";

export function IPhone({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("iphone", className)} aria-hidden="true">
      <div className="iphone-bezel">
        <div className="iphone-screen">
          <div className="island" />
          {children}
        </div>
      </div>
    </div>
  );
}

export function WatchFace({ title, artist }: { title: string; artist: string }) {
  return (
    <div className="watch" aria-hidden="true">
      <div className="watch-bezel">
        <div className="watch-screen">
          <p className="watch-source">iPhone</p>
          <p className="watch-title">{title}</p>
          <p className="watch-artist">{artist}</p>
        </div>
      </div>
    </div>
  );
}

export function CaptionBar({
  mode,
  clock = sample.clock,
}: {
  mode: "listening" | "alert" | "muted";
  clock?: string;
}) {
  return (
    <div className={cn("caption-bar", `is-${mode}`)} aria-hidden="true">
      <div className="caption-meta">
        {mode === "listening" ? (
          <span>
            <i className="listen-dot" />
            LISTENING · ROOM 304 · EN
          </span>
        ) : null}
        {mode === "alert" ? (
          <span className="caption-alert">
            <Diamond size={11} /> HEARD YOUR NAME
          </span>
        ) : null}
        {mode === "muted" ? (
          <span>
            <PauseMark size={11} /> MUTED
          </span>
        ) : null}
        <span className="nums">— BYTES SENT · {clock}</span>
      </div>
      {mode === "muted" ? (
        <p className="caption-muted">Muted · not listening</p>
      ) : (
        <>
          <p className="caption-prev">
            {mode === "alert" ? "Your name" : sample.previous}
          </p>
          <p className="caption-now">
            {mode === "alert" ? sample.alert : sample.current}
          </p>
        </>
      )}
    </div>
  );
}
