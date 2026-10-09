import { useEffect, useRef } from "react";

const SAGE = "169, 184, 156";
const GLOW = "127, 179, 213";
const RING_COUNT = 5;
const RING_PERIOD = 16000;

/**
 * A few expanding strokes and one soft radial glow.
 * Pauses off-screen and when the tab is hidden.
 */
export function ListeningField() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    const parent = canvas?.parentElement;
    if (!canvas || !parent) return;
    const context = canvas.getContext("2d", { alpha: true });
    if (!context) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let frame = 0;
    let visible = true;
    let disposed = false;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      const width = parent.clientWidth;
      const height = parent.clientHeight;
      canvas.width = Math.max(1, Math.floor(width * dpr));
      canvas.height = Math.max(1, Math.floor(height * dpr));
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const origin = () => {
      const bounds = parent.getBoundingClientRect();
      const mark = document.querySelector(".nav-brand img");
      if (mark) {
        const box = mark.getBoundingClientRect();
        return {
          x: box.left + box.width * 0.62 - bounds.left,
          y: box.top + box.height * 0.42 - bounds.top,
        };
      }
      return { x: 72, y: 36 };
    };

    const draw = (now: number) => {
      if (disposed) return;
      const width = parent.clientWidth;
      const height = parent.clientHeight;
      context.clearRect(0, 0, width, height);
      const point = origin();
      const wave = 0.5 + 0.5 * Math.sin((now / 4000) * Math.PI * 2);
      const breath = reduced ? 0.08 : 0.05 + 0.06 * wave;
      const alpha = Math.min(0.11, breath);
      const glow = context.createRadialGradient(point.x, point.y, 0, point.x, point.y, 240);
      glow.addColorStop(0, `rgba(${GLOW}, ${alpha})`);
      glow.addColorStop(1, `rgba(${GLOW}, 0)`);
      context.fillStyle = glow;
      context.beginPath();
      context.arc(point.x, point.y, 240, 0, Math.PI * 2);
      context.fill();

      const reach = Math.hypot(width, height);
      for (let index = 0; index < RING_COUNT; index += 1) {
        const phase = reduced ? index / RING_COUNT : ((now / RING_PERIOD) + index / RING_COUNT) % 1;
        const radius = 12 + phase * reach;
        if (phase > 0.92) continue;
        const ring = 0.1 - phase * 0.04;
        context.beginPath();
        context.arc(point.x, point.y, radius, 0, Math.PI * 2);
        context.strokeStyle = `rgba(${SAGE}, ${ring})`;
        context.lineWidth = 1;
        context.stroke();
      }

      if (!reduced && visible && !document.hidden) {
        frame = requestAnimationFrame(draw);
      }
    };

    resize();
    const resizeObserver = new ResizeObserver(() => {
      resize();
      if (reduced) draw(0);
    });
    resizeObserver.observe(parent);

    const intersection = new IntersectionObserver(([entry]) => {
      visible = Boolean(entry?.isIntersecting);
      cancelAnimationFrame(frame);
      if (visible) frame = requestAnimationFrame(draw);
    });
    intersection.observe(parent);

    const onVisibility = () => {
      cancelAnimationFrame(frame);
      if (!document.hidden && visible) frame = requestAnimationFrame(draw);
    };
    document.addEventListener("visibilitychange", onVisibility);
    frame = requestAnimationFrame(draw);

    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      resizeObserver.disconnect();
      intersection.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, []);

  return <canvas ref={ref} className="listening-field" aria-hidden="true" />;
}
