"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Difficulty, LockIcon } from "@/components/ProblemBits";
import { request } from "@/lib/api";
import { CATEGORY_LABELS, PROGRESS_LABELS } from "@/lib/labels";
import { useSession } from "@/lib/session";
import type { LearningPath } from "@/lib/types";

const DIFFICULTY_BORDER = { easy: "border-easy", medium: "border-medium", hard: "border-hard" } as const;
const DIFFICULTY_FILL = { easy: "bg-easy", medium: "bg-medium", hard: "bg-hard" } as const;

/** One path: its tasks in order, as waypoints on a vertical trail. */
export function PathDetail({ initial }: { initial: LearningPath }) {
  const session = useSession();
  const [path, setPath] = useState(initial);

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

  const next = path.tasks.find((task) => task.id === path.next_task_id);
  const total = path.tasks.length;

  return (
    <>
      <div className="flex flex-col gap-3">
        <Link href="/tasks" className="self-start text-sm">
          All paths
        </Link>
        <h1 className="text-4xl">{path.title}</h1>
        <p className="max-w-[60ch] text-lg text-muted">{path.summary}</p>
        <div className="mt-2 flex flex-wrap items-center gap-4">
          {next ? (
            <Link href={`/tasks/${next.id}?path=${path.id}`} className="btn-primary px-5 py-2.5 text-base">
              {path.solved > 0 ? `Continue with ${next.title}` : `Start with ${next.title}`}
            </Link>
          ) : (
            <p className="font-medium text-success">You&apos;ve solved every task on this path.</p>
          )}
          <span className="text-muted">
            {path.solved} of {total} {total === 1 ? "task" : "tasks"} solved
          </span>
        </div>
      </div>

      <ol className="flex flex-col">
        {path.tasks.map((task, index) => {
          const solved = task.progress === "solved";
          const last = index === total - 1;
          return (
            <li key={task.id} className="grid grid-cols-[2rem_minmax(0,1fr)] gap-x-4">
              {/* The trail: a waypoint per task, joined by a line down to the next one. */}
              <div className="flex flex-col items-center" aria-hidden="true">
                <span
                  className={`mt-1.5 size-4 shrink-0 rounded-full border-2 ${DIFFICULTY_BORDER[task.difficulty]} ${
                    solved ? DIFFICULTY_FILL[task.difficulty] : "bg-page"
                  }`}
                />
                {!last && <span className="w-0.5 flex-1 bg-line" />}
              </div>
              <div className={`flex flex-col gap-2 ${last ? "" : "pb-8"}`}>
                <h2 className="flex flex-wrap items-baseline gap-x-3 text-xl">
                  <span className="text-muted">{index + 1}</span>
                  <Link href={`/tasks/${task.id}?path=${path.id}`} className="text-ink no-underline hover:underline">
                    {task.title}
                  </Link>
                </h2>
                <p className="max-w-[64ch] text-muted">{task.summary}</p>
                <p className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
                  <Difficulty level={task.difficulty} />
                  <span className="text-muted">
                    {CATEGORY_LABELS[task.category] ?? task.category} task, about {task.est_minutes} minutes
                  </span>
                  {task.access === "paid" && (
                    <span className="inline-flex items-center gap-1.5 text-muted">
                      <LockIcon label="" />
                      Lifetime and Pro
                    </span>
                  )}
                  {session.status === "signed_in" && (
                    <span className={solved ? "text-success" : "text-muted"}>
                      {PROGRESS_LABELS[task.progress ?? "not_started"]}
                      {task.best_result ? `, best ${task.best_result.label}` : ""}
                    </span>
                  )}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </>
  );
}
