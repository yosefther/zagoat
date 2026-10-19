"use client";

import { useSyncExternalStore } from "react";

import { DEFAULT_THEME } from "@/lib/theme";

/** The theme showing now: <html data-theme>, which defaults to dark. */
function read(): "light" | "dark" {
  return document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
}

function subscribe(onChange: () => void) {
  const observer = new MutationObserver(onChange);
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  return () => observer.disconnect();
}

export function useResolvedTheme(): "light" | "dark" {
  return useSyncExternalStore(subscribe, read, () => DEFAULT_THEME);
}
