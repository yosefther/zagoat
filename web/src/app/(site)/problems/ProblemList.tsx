import { ProblemTable } from "./ProblemTable";
import { serverRequest } from "@/lib/api";
import type { ProblemSummary } from "@/lib/types";

/** Public list, rendered on the server so search engines see every task. */
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
    return <p className="text-muted">No problems are published yet. Check back soon.</p>;
  }
  return <ProblemTable initial={problems} />;
}
