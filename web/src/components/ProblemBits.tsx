import { DIFFICULTY_LABELS, PROGRESS_LABELS } from "@/lib/labels";
import type { ProblemSummary } from "@/lib/types";

type Level = ProblemSummary["difficulty"];

const DIFFICULTY_CLASSES = {
  easy: "text-easy",
  medium: "text-medium",
  hard: "text-hard",
} as const;

const PEAKS: Record<Level, number> = { easy: 1, medium: 2, hard: 3 };

/** Difficulty as a grade: one to three peaks, plus the word, in the difficulty's color. */
export function Difficulty({ level }: { level: Level }) {
  const filled = PEAKS[level];
  return (
    <span className={`inline-flex items-center gap-1.5 font-medium ${DIFFICULTY_CLASSES[level]}`}>
      <svg width="27" height="10" viewBox="0 0 27 10" aria-hidden="true" className="shrink-0">
        {[0, 1, 2].map((i) => (
          <path
            key={i}
            d={`M${i * 9 + 0.75} 9.25 L${i * 9 + 4.5} 0.75 L${i * 9 + 8.25} 9.25 Z`}
            fill={i < filled ? "currentColor" : "none"}
            stroke="currentColor"
            strokeWidth="1.2"
            strokeLinejoin="round"
            opacity={i < filled ? 1 : 0.45}
          />
        ))}
      </svg>
      {DIFFICULTY_LABELS[level]}
    </span>
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
