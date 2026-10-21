"use client";

import { DEFAULT_THEME, THEME_STORAGE_KEY, type Theme } from "@/lib/theme";

function currentTheme(): Theme {
  const value = document.documentElement.getAttribute("data-theme");
  return value === "light" || value === "dark" ? value : DEFAULT_THEME;
}

function setTheme(theme: Theme) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Storage can be blocked; the theme still applies to this page view.
  }
  document.documentElement.setAttribute("data-theme", theme);
}

/**
 * Dark by default; one button switches to light and back. Both icons and labels are always
 * rendered and CSS shows the right pair, so the server HTML matches whatever theme the
 * visitor saved (no hydration mismatch).
 */
export function ThemeToggle() {
  return (
    <button
      type="button"
      onClick={() => setTheme(currentTheme() === "dark" ? "light" : "dark")}
      className="btn-quiet px-2"
    >
      <span className="light:hidden">
        <SunIcon />
        <span className="sr-only">Switch to light theme</span>
      </span>
      <span className="hidden light:inline">
        <MoonIcon />
        <span className="sr-only">Switch to dark theme</span>
      </span>
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
