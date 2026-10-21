"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PathArt, type PathArtKind } from "@/components/PathArt";
import { Difficulty } from "@/components/ProblemBits";
import { request } from "@/lib/api";
import { CATEGORY_LABELS } from "@/lib/labels";
import { useSession } from "@/lib/session";
import type { LearningPath, ProblemSummary } from "@/lib/types";

/** Every path as a card. Public on the server; progress is added here. */
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
    <ul className="grid grid-cols-[minmax(0,1fr)] gap-4 lg:grid-cols-2">
      {paths.map((path) => (
        <PathCard key={path.id} path={path} />
      ))}
    </ul>
  );
}

const ART_KINDS: readonly string[] = ["rag", "evals", "training", "serving"];
const LEVELS: ProblemSummary["difficulty"][] = ["easy", "medium", "hard"];

/** A path's art follows its tasks: one category gets that scene, a mix gets the mixed one. */
function artKind(path: LearningPath): PathArtKind {
  const categories = new Set(path.tasks.map((task) => task.category));
  const [only] = categories;
  return categories.size === 1 && ART_KINDS.includes(only) ? (only as PathArtKind) : "mixed";
}

function PathCard({ path }: { path: LearningPath }) {
  const total = path.tasks.length;
  const minutes = path.tasks.reduce((sum, task) => sum + task.est_minutes, 0);
  const hardest = LEVELS.findLast((level) => path.tasks.some((task) => task.difficulty === level));
  const categories = [...new Set(path.tasks.map((task) => task.category))];
  const started = path.tasks.some((task) => task.progress && task.progress !== "not_started");
  const done = total > 0 && path.solved === total;

  return (
    <li>
      <Link
        href={`/paths/${path.id}`}
        className="group grid h-full grid-cols-[6.5rem_minmax(0,1fr)] gap-4 border border-line bg-panel p-4 text-ink no-underline transition-colors duration-150 hover:border-field sm:grid-cols-[11rem_minmax(0,1fr)] sm:gap-6"
      >
        <span className="flex aspect-square items-center justify-center self-start bg-raised p-2">
          <PathArt kind={artKind(path)} className="w-full" />
        </span>
        <span className="flex min-w-0 flex-col gap-2 py-1">
          <span className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted">
            {done ? (
              <span className="bg-brand px-2 font-medium text-on-brand">Completed</span>
            ) : started ? (
              <span className="bg-raised px-2 font-medium text-ink group-hover:bg-panel">In progress</span>
            ) : null}
            <span>{categories.map((category) => CATEGORY_LABELS[category] ?? category).join(" and ")}</span>
            <span>
              {total} {total === 1 ? "task" : "tasks"}
            </span>
          </span>
          <span className="font-heading text-2xl leading-tight font-bold group-hover:underline">{path.title}</span>
          <span className="line-clamp-3 text-muted">{path.summary}</span>
          <span className="mt-auto flex items-center gap-4 pt-2 text-sm">
            {started ? (
              <Progress path={path} />
            ) : (
              <span className="flex flex-wrap items-center gap-x-4 gap-y-1 text-muted">
                {hardest && <Difficulty level={hardest} />}
                <span>About {minutes} min</span>
              </span>
            )}
            <svg viewBox="0 0 16 16" className="ml-auto size-4 shrink-0 text-muted transition-transform duration-150 group-hover:translate-x-0.5 group-hover:text-ink" aria-hidden="true">
              <path d="M6 3l5 5-5 5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
        </span>
      </Link>
    </li>
  );
}

/** A plain bar that fills with solved tasks only; started ones are counted in the text. */
function Progress({ path }: { path: LearningPath }) {
  const total = path.tasks.length;
  const started = path.tasks.filter(
    (task) => task.progress === "attempted" || task.progress === "in_progress",
  ).length;
  return (
    <span className="flex min-w-0 flex-1 flex-wrap items-center gap-x-3 gap-y-1">
      <span
        role="progressbar"
        aria-label="Tasks solved"
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={path.solved}
        className="h-1.5 min-w-20 max-w-48 flex-1 overflow-hidden rounded-full bg-line"
      >
        <span className="block h-full rounded-full bg-brand" style={{ width: `${(path.solved / total) * 100}%` }} />
      </span>
      <span className="text-muted">
        {path.solved} of {total} solved
        {started > 0 && `, ${started} started`}
      </span>
    </span>
  );
}
