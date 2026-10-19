import { DIFFICULTY_LABELS, PROGRESS_LABELS } from "@/lib/labels";
import type { ProblemSummary } from "@/lib/types";

const DIFFICULTY_CLASSES = {
  easy: "text-easy",
  medium: "text-medium",
  hard: "text-hard",
} as const;

/** Difficulty as colored text (never a filled pill). */
export function Difficulty({ level }: { level: ProblemSummary["difficulty"] }) {
  return (
    <span className={`font-medium ${DIFFICULTY_CLASSES[level]}`}>{DIFFICULTY_LABELS[level]}</span>
  );
}

/** Solved, attempted or not started, as an icon with an accessible label. */
export function StatusIcon({ progress }: { progress: ProblemSummary["progress"] }) {
  const state = progress ?? "not_started";
  const label = PROGRESS_LABELS[state];
  if (state === "solved") {
    return (
      <svg width="16" height="16" viewBox="0 0 16 16" role="img" aria-label={label} className="text-success">
        <title>{label}</title>
        <path d="M3 8.5l3 3 7-7" fill="none" stroke="currentColor" strokeWidth="2" />
      </svg>
    );
  }
  if (state === "attempted" || state === "in_progress") {
    return (
      <svg width="16" height="16" viewBox="0 0 16 16" role="img" aria-label={label} className="text-warning">
        <title>{label}</title>
        <circle cx="8" cy="8" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
        <path d="M8 2.5a5.5 5.5 0 0 1 0 11z" fill="currentColor" />
      </svg>
    );
  }
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" role="img" aria-label={label} className="text-field">
      <title>{label}</title>
      <circle cx="8" cy="8" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

export function LockIcon({ label = "Lifetime and Pro" }: { label?: string }) {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" role="img" aria-label={label} className="shrink-0 text-muted">
      <title>{label}</title>
      <rect x="3" y="7" width="10" height="7" rx="1" fill="currentColor" />
      <path d="M5 7V5a3 3 0 0 1 6 0v2" fill="none" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}
