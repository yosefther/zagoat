import { Difficulty, LockIcon } from "@/components/ProblemBits";
import { CATEGORY_LABELS } from "@/lib/labels";
import type { ProblemSummary } from "@/lib/types";

/** The grade, then a plain phrase: "RAG task, about 45 minutes". */
export function ProblemMeta({
  problem,
}: {
  problem: Pick<ProblemSummary, "category" | "difficulty" | "est_minutes" | "access">;
}) {
  const category = CATEGORY_LABELS[problem.category] ?? problem.category;
  return (
    <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
      <Difficulty level={problem.difficulty} />
      <span className="text-muted">
        {category} task, about {problem.est_minutes} minutes
      </span>
      {problem.access === "paid" && (
        <span className="inline-flex items-center gap-1.5 text-muted">
          <LockIcon label="" />
          Lifetime and Pro
        </span>
      )}
    </p>
  );
}
