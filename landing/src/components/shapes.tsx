export function Diamond({ size = 12 }: { size?: number }) {
  return (
    <svg viewBox="0 0 16 16" width={size} height={size} aria-hidden="true">
      <path d="M8 1 L15 8 L8 15 L1 8Z" fill="currentColor" />
    </svg>
  );
}

export function ListenMark({ size = 12 }: { size?: number }) {
  return (
    <svg viewBox="0 0 16 16" width={size} height={size} aria-hidden="true">
      <circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" strokeWidth="2" />
      <circle cx="8" cy="8" r="2.5" fill="currentColor" />
    </svg>
  );
}

export function PlayMark({ size = 12 }: { size?: number }) {
  return (
    <svg viewBox="0 0 16 16" width={size} height={size} aria-hidden="true">
      <path d="M5 2.5 L13.5 8 L5 13.5Z" fill="currentColor" />
    </svg>
  );
}

export function PauseMark({ size = 12 }: { size?: number }) {
  return (
    <svg viewBox="0 0 16 16" width={size} height={size} aria-hidden="true">
      <rect x="3" y="2" width="3.2" height="12" fill="currentColor" />
      <rect x="9.8" y="2" width="3.2" height="12" fill="currentColor" />
    </svg>
  );
}

export function PrevIcon() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" aria-hidden="true">
      <path d="M11 6v12L2 12zM21 6v12l-9-6z" />
    </svg>
  );
}

export function NextIcon() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor" aria-hidden="true">
      <path d="M13 6v12l9-6zM3 6v12l9-6z" />
    </svg>
  );
}
