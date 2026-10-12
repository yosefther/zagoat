"use client";

import { useSyncExternalStore } from "react";

import { THEME_STORAGE_KEY, type ThemeChoice } from "@/lib/theme";

const listeners = new Set<() => void>();

function readChoice(): ThemeChoice {
  try {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    return saved === "light" || saved === "dark" ? saved : "auto";
  } catch {
    return "auto";
  }
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function applyChoice(choice: ThemeChoice) {
  try {
    if (choice === "auto") localStorage.removeItem(THEME_STORAGE_KEY);
    else localStorage.setItem(THEME_STORAGE_KEY, choice);
  } catch {
    // Storage can be blocked; the choice still applies to this page view.
  }
  if (choice === "auto") document.documentElement.removeAttribute("data-theme");
  else document.documentElement.setAttribute("data-theme", choice);
  listeners.forEach((listener) => listener());
}

export function ThemeToggle() {
  const choice = useSyncExternalStore(subscribe, readChoice, () => "auto" as ThemeChoice);
  return (
    <label className="inline-flex items-center gap-2 text-sm text-muted">
      Theme
      <select
        className="rounded-md border border-field bg-surface px-2 py-1 text-ink"
        value={choice}
        onChange={(event) => applyChoice(event.target.value as ThemeChoice)}
      >
        <option value="auto">Match system</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </label>
  );
}
