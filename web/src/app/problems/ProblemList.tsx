import Link from "next/link";

import { ProgressBadge } from "@/app/problems/ProgressBadge";
import { ProblemMeta } from "@/components/ProblemMeta";
import { serverRequest } from "@/lib/api";
import type { ProblemSummary } from "@/lib/types";

export async function ProblemList() {
  let problems: ProblemSummary[] | null;
  try {
    problems = await serverRequest<ProblemSummary[]>("/problems");
  } catch {
    problems = null;
  }
  if (problems === null) {
    return (
      <p role="alert" className="text-danger">
        We couldn&apos;t load the problems. Reload the page in a minute.
      </p>
    );
  }
  if (problems.length === 0) {
    return <p className="text-muted">No problems are published yet.</p>;
  }
  return (
    <ul className="grid gap-4 md:grid-cols-2">
      {problems.map((problem) => (
        <li key={problem.id} className="card flex min-w-0 flex-col gap-2 p-5">
          <div className="flex items-start justify-between gap-4">
            <ProblemMeta problem={problem} />
            <ProgressBadge problemId={problem.id} />
          </div>
          <h2 className="text-lg font-bold">
            <Link href={`/problems/${problem.id}`} className="text-ink">
              {problem.title}
            </Link>
          </h2>
          <p className="text-sm text-muted">{problem.summary}</p>
        </li>
      ))}
    </ul>
  );
}
