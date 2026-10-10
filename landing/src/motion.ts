export const easeIn = [0.2, 0, 0, 1] as const;
export const easeState = [0.4, 0, 0.6, 1] as const;

let loggedPause = false;
let loggedResume = false;

export function logRaf(state: "pause" | "resume") {
  if (state === "pause" && !loggedPause) {
    loggedPause = true;
    console.info("[earshot] rAF pause");
  }
  if (state === "resume" && !loggedResume) {
    loggedResume = true;
    console.info("[earshot] rAF resume");
  }
}

export function canvasDensity() {
  const cores = navigator.hardwareConcurrency || 8;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  return cores <= 4 ? dpr * 0.5 : dpr;
}
