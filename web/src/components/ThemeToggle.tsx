"use client";

import { useSyncExternalStore } from "react";

import { DEFAULT_THEME, THEME_STORAGE_KEY, type Theme } from "@/lib/theme";

const listeners = new Set<() => void>();

function readTheme(): Theme {
  const current = document.documentElement.getAttribute("data-theme");
  return current === "light" || current === "dark" ? current : DEFAULT_THEME;
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function setTheme(theme: Theme) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Storage can be blocked; the theme still applies to this page view.
  }
  document.documentElement.setAttribute("data-theme", theme);
  listeners.forEach((listener) => listener());
}

/** Dark by default (section 12); one button switches to light and back. */
export function ThemeToggle() {
  const theme = useSyncExternalStore(subscribe, readTheme, () => DEFAULT_THEME);
  const next = theme === "dark" ? "light" : "dark";
  return (
    <button
      type="button"
      onClick={() => setTheme(next)}
      className="btn-quiet px-2"
      aria-label={`Switch to ${next} theme`}
      title={`Switch to ${next} theme`}
    >
      {theme === "dark" ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}

function SunIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
    </svg>
  );
}
