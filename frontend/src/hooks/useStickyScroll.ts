import { useEffect, useRef } from "react";
import type { RefObject } from "react";

// Far enough from the bottom to mean the reader went looking for older text,
// near enough that a line arriving mid-scroll does not count as leaving.
const SLACK_PX = 24;

function atBottom(element: HTMLElement): boolean {
  return element.scrollHeight - element.scrollTop - element.clientHeight <= SLACK_PX;
}

/** Holds a growing box at its newest line, until the reader scrolls back through it. */
export function useStickyScroll<E extends HTMLElement>(content: string): RefObject<E> {
  const box = useRef<E>(null);
  const following = useRef(true);

  useEffect(() => {
    const element = box.current;
    if (!element) return;
    const follow = (): void => {
      following.current = atBottom(element);
    };
    element.addEventListener("scroll", follow, { passive: true });
    return () => element.removeEventListener("scroll", follow);
  }, []);

  useEffect(() => {
    const element = box.current;
    if (element && following.current) element.scrollTop = element.scrollHeight;
  }, [content]);

  return box;
}
