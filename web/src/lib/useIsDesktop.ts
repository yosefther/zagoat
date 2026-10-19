"use client";

import { useSyncExternalStore } from "react";

const QUERY = "(min-width: 1024px)";

/** True on screens wide enough to solve (the workspace); false on the server and phones. */
export function useIsDesktop(): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const media = window.matchMedia(QUERY);
      media.addEventListener("change", onChange);
      return () => media.removeEventListener("change", onChange);
    },
    () => window.matchMedia(QUERY).matches,
    () => false,
  );
}
