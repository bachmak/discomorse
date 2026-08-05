import type { ItemWindow } from "./window";

// The trace is a step function of sample index, and a column shows its mean over
// the slice it covers: whole samples inside the column weigh fully, the two its
// fractional edges cut into weigh the part they cover. A window that slides by a
// fraction of a sample therefore moves the trace by a fraction of a pixel
// instead of snapping to the next one.
function meanOver(levels: readonly number[], from: number, to: number): number {
  let area = 0;
  for (let i = Math.max(0, Math.floor(from)); i < Math.min(levels.length, to); i++) {
    area += levels[i] * (Math.min(i + 1, to) - Math.max(i, from));
  }
  return area / (to - from);
}

/** One value per pixel column of the window, read at the resolution that column has. */
export function columnMeans(
  levels: readonly number[],
  window: ItemWindow,
  columns: number,
): number[] {
  const perColumn = (window.to - window.from) / columns;
  return Array.from({ length: columns }, (_unused, x) =>
    meanOver(levels, window.from + x * perColumn, window.from + (x + 1) * perColumn),
  );
}
