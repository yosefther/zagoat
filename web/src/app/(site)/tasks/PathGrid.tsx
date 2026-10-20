"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PathTrail } from "@/components/PathTrail";
import { request } from "@/lib/api";
import { useSession } from "@/lib/session";
import type { LearningPath } from "@/lib/types";

/** The paths grid. Public on the server; the signed-in user's progress is added here. */
export function PathGrid({ initial }: { initial: LearningPath[] }) {
  const session = useSession();
  const [paths, setPaths] = useState(initial);

  useEffect(() => {
    if (session.status !== "signed_in") return;
    let active = true;
    request<LearningPath[]>("/paths")
      .then((rows) => active && setPaths(rows))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [session.status]);

  return (
    <ul className="grid grid-cols-[repeat(auto-fill,minmax(min(100%,20rem),1fr))] gap-px overflow-hidden rounded-sm bg-line">
      {paths.map((path) => (
        <PathTile key={path.id} path={path} />
      ))}
    </ul>
  );
}

function PathTile({ path }: { path: LearningPath }) {
  const total = path.tasks.length;
  const next = path.tasks.find((task) => task.id === path.next_task_id);
  const done = path.solved === total;
  const action = done ? "Review this path" : path.solved > 0 ? "Continue this path" : "Start this path";
  const actionHref = next ? `/tasks/${next.id}?path=${path.id}` : `/paths/${path.id}`;

  return (
    <li className="flex flex-col gap-4 bg-panel p-6">
      <div className="flex flex-col gap-2">
        <h2 className="text-2xl">
          <Link href={`/paths/${path.id}`} className="text-ink no-underline hover:underline">
            {path.title}
          </Link>
        </h2>
        <p className="text-muted">{path.summary}</p>
      </div>
      <div className="flex flex-col gap-2">
        <PathTrail tasks={path.tasks} />
        <p className="text-sm text-muted">
          {path.solved} of {total} {total === 1 ? "task" : "tasks"} solved
        </p>
      </div>
      <div className="mt-auto flex flex-col gap-3">
        {next && (
          <p className="text-sm">
            <span className="text-muted">Next: </span>
            {next.title}
          </p>
        )}
        <Link href={actionHref} className={done ? "btn-secondary self-start" : "btn-primary self-start"}>
          {action}
        </Link>
      </div>
    </li>
  );
}
