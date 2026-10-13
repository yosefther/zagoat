import { ACCESS_LABELS, CATEGORY_LABELS } from "@/lib/labels";
import type { ProblemSummary } from "@/lib/types";

export function ProblemMeta({ problem }: { problem: ProblemSummary }) {
  return (
    <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs font-medium tracking-wide text-muted uppercase">
      <span>{CATEGORY_LABELS[problem.category] ?? problem.category}</span>
      <span aria-hidden="true">·</span>
      <span>{problem.difficulty}</span>
      <span aria-hidden="true">·</span>
      <span>{problem.est_minutes} min</span>
      {problem.access === "paid" && (
        <span className="rounded-full border border-field px-2 py-0.5 normal-case tracking-normal">
          {ACCESS_LABELS.paid}
        </span>
      )}
    </p>
  );
}
