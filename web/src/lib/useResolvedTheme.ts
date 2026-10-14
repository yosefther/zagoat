"use client";

import { useSyncExternalStore } from "react";

/** The theme actually showing: a saved choice on <html data-theme>, else the system setting. */
function read(): "light" | "dark" {
  const forced = document.documentElement.getAttribute("data-theme");
  if (forced === "light" || forced === "dark") return forced;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function subscribe(onChange: () => void) {
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  media.addEventListener("change", onChange);
  return () => {
    observer.disconnect();
    media.removeEventListener("change", onChange);
  };
}

export function useResolvedTheme(): "light" | "dark" {
  return useSyncExternalStore(subscribe, read, () => "light");
}
