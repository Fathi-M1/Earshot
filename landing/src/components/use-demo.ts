import { useEffect, useRef, useState, type RefObject } from "react";
import { usePrefersReducedMotion } from "@/components/use-reduced-motion";

export function useInView<T extends HTMLElement>(threshold = 0.2) {
  const ref = useRef<T>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      ([entry]) => setInView(Boolean(entry?.isIntersecting)),
      { threshold },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [threshold]);

  return [ref, inView] as const;
}

export function useDemoActive<T extends HTMLElement>(threshold = 0.4) {
  const reduced = usePrefersReducedMotion();
  const [ref, inView] = useInView<T>(threshold);
  const [hover, setHover] = useState(false);
  return {
    ref: ref as RefObject<T | null>,
    active: !reduced && (inView || hover),
    reduced,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
  };
}
