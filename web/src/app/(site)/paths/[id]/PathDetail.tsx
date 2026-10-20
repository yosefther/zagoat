"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Difficulty, LockIcon, StatusIcon } from "@/components/ProblemBits";
import { request } from "@/lib/api";
import { CATEGORY_LABELS, DIFFICULTY_LABELS, PROGRESS_LABELS } from "@/lib/labels";
import { useSession } from "@/lib/session";
import type { LearningPath, ProblemSummary } from "@/lib/types";

type Status = "all" | "solved" | "attempted" | "not_started";

function statusOf(task: ProblemSummary): Exclude<Status, "all"> {
  if (task.progress === "solved") return "solved";
  if (task.progress === "attempted" || task.progress === "in_progress") return "attempted";
  return "not_started";
}

/** One path as a list of its tasks, in climbing order, with filters. */
export function PathDetail({ initial }: { initial: LearningPath }) {
  const session = useSession();
  const [path, setPath] = useState(initial);
  const [difficulty, setDifficulty] = useState("all");
  const [status, setStatus] = useState<Status>("all");

  useEffect(() => {
    if (session.status !== "signed_in") return;
    let active = true;
    request<LearningPath>(`/paths/${encodeURIComponent(initial.id)}`)
      .then((data) => active && setPath(data))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [initial.id, session.status]);

  const signedIn = session.status === "signed_in";
  const total = path.tasks.length;
  const next = path.tasks.find((task) => task.id === path.next_task_id);

  // Keep each task's place on the path, even when filters hide some.
  const rows = useMemo(
    () =>
      path.tasks
        .map((task, index) => ({ task, step: index + 1 }))
        .filter(
          ({ task }) =>
            (difficulty === "all" || task.difficulty === difficulty) &&
            (status === "all" || statusOf(task) === status),
        ),
    [path.tasks, difficulty, status],
  );

  const selectClass = "rounded-md border border-field bg-panel px-2.5 py-1.5 text-sm text-ink";

  return (
    <>
      <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
        <div className="flex flex-col gap-2">
          <Link href="/tasks" className="self-start text-sm">
            All paths
          </Link>
          <h1 className="text-4xl">{path.title}</h1>
          <p className="max-w-[60ch] text-muted">{path.summary}</p>
          <p className="text-sm text-muted">
            {signedIn
              ? `${path.solved} of ${total} ${total === 1 ? "task" : "tasks"} solved`
              : `${total} ${total === 1 ? "task" : "tasks"}`}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="sr-only" htmlFor="path-difficulty">
            Difficulty
          </label>
          <select
            id="path-difficulty"
            className={selectClass}
            value={difficulty}
            onChange={(event) => setDifficulty(event.target.value)}
          >
            <option value="all">All difficulties</option>
            {Object.entries(DIFFICULTY_LABELS).map(([key, label]) => (
              <option key={key} value={key}>
                {label}
              </option>
            ))}
          </select>
          {signedIn && (
            <>
              <label className="sr-only" htmlFor="path-status">
                Status
              </label>
              <select
                id="path-status"
                className={selectClass}
                value={status}
                onChange={(event) => setStatus(event.target.value as Status)}
              >
                <option value="all">Any status</option>
                <option value="solved">{PROGRESS_LABELS.solved}</option>
                <option value="attempted">{PROGRESS_LABELS.attempted}</option>
                <option value="not_started">{PROGRESS_LABELS.not_started}</option>
              </select>
            </>
          )}
          {next && (
            <Link href={`/tasks/${next.id}?path=${path.id}`} className="btn-primary">
              {path.solved > 0 ? "Continue the path" : "Open the first task"}
            </Link>
          )}
        </div>
      </div>

      <ol className="overflow-hidden rounded-sm bg-panel">
        {rows.map(({ task, step }) => (
          <li key={task.id} className="border-b border-line last:border-b-0">
            <Link
              href={`/tasks/${task.id}?path=${path.id}`}
              className="grid grid-cols-[1.25rem_minmax(0,1fr)] items-center gap-x-3 px-4 py-4 sm:grid-cols-[1.5rem_minmax(0,1fr)_auto] sm:gap-x-4 sm:px-5 text-ink no-underline hover:bg-raised"
            >
              <StatusIcon progress={task.progress} />
              <div className="flex min-w-0 flex-col gap-1">
                <p className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <span className="text-muted tabular-nums">{step}</span>
                  <span className="font-heading text-xl font-bold">{task.title}</span>
                  <Difficulty level={task.difficulty} />
                  {task.access === "paid" && (
                    <span className="inline-flex items-center gap-1.5 text-sm text-muted">
                      <LockIcon label="" />
                      Lifetime and Pro
                    </span>
                  )}
                </p>
                <p className="line-clamp-2 text-sm text-muted sm:line-clamp-1">
                  {CATEGORY_LABELS[task.category] ?? task.category} task. {task.summary}
                </p>
                <p className="text-sm text-muted sm:hidden">
                  About {task.est_minutes} min{task.best_result ? `, best ${task.best_result.label}` : ""}
                </p>
              </div>
              <div className="hidden flex-col items-end gap-1 text-sm whitespace-nowrap sm:flex">
                <span className="text-muted">about {task.est_minutes} min</span>
                {task.best_result && <span>best {task.best_result.label}</span>}
              </div>
            </Link>
          </li>
        ))}
        {rows.length === 0 && (
          <li className="p-6 text-sm text-muted">
            No tasks on this path match these filters. Pick a different difficulty or status.
          </li>
        )}
      </ol>
    </>
  );
}
