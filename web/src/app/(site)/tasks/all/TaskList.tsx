import { TaskTable } from "./TaskTable";
import { serverRequest } from "@/lib/api";
import type { ProblemSummary } from "@/lib/types";

/** Every task, rendered on the server so search engines see them all. */
export async function TaskList() {
  let problems: ProblemSummary[] | null;
  try {
    problems = await serverRequest<ProblemSummary[]>("/problems");
  } catch {
    problems = null;
  }
  if (problems === null) {
    return (
      <p role="alert" className="text-danger">
        We couldn&apos;t load the tasks. Reload the page in a minute.
      </p>
    );
  }
  if (problems.length === 0) {
    return <p className="text-muted">No tasks are published yet. Check back soon.</p>;
  }
  return <TaskTable initial={problems} />;
}
