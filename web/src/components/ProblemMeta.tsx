import { Difficulty, LockIcon } from "@/components/ProblemBits";
import { CATEGORY_LABELS } from "@/lib/labels";
import type { ProblemSummary } from "@/lib/types";

/** "RAG · Medium · 45 min", in sentence case, with difficulty in its color. */
export function ProblemMeta({
  problem,
}: {
  problem: Pick<ProblemSummary, "category" | "difficulty" | "est_minutes" | "access">;
}) {
  return (
    <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted">
      <span>{CATEGORY_LABELS[problem.category] ?? problem.category}</span>
      <span aria-hidden="true">·</span>
      <Difficulty level={problem.difficulty} />
      <span aria-hidden="true">·</span>
      <span>{problem.est_minutes} min</span>
      {problem.access === "paid" && (
        <>
          <span aria-hidden="true">·</span>
          <span className="inline-flex items-center gap-1">
            <LockIcon label="" />
            Lifetime and Pro
          </span>
        </>
      )}
    </p>
  );
}
