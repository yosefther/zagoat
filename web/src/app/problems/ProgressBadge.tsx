"use client";

import { useEffect, useState } from "react";

import { request } from "@/lib/api";
import { PROGRESS_LABELS } from "@/lib/labels";
import { useSession } from "@/lib/session";
import type { ProblemSummary } from "@/lib/types";

type ProgressMap = Record<string, ProblemSummary["progress"]>;

// One request per page load, shared by every badge on the list.
let shared: Promise<ProgressMap> | null = null;

function loadProgress(): Promise<ProgressMap> {
  shared ??= request<ProblemSummary[]>("/problems").then((problems) =>
    Object.fromEntries(problems.map((p) => [p.id, p.progress])),
  );
  return shared;
}

/** The signed-in user's progress on one problem, shown on the problem list. */
export function ProgressBadge({ problemId }: { problemId: string }) {
  const session = useSession();
  const [progress, setProgress] = useState<ProblemSummary["progress"]>(null);

  useEffect(() => {
    if (session.status !== "signed_in") return;
    let active = true;
    loadProgress()
      .then((map) => active && setProgress(map[problemId] ?? null))
      .catch(() => {
        shared = null;
      });
    return () => {
      active = false;
    };
  }, [problemId, session.status]);

  if (!progress || progress === "not_started") return null;
  return (
    <span
      className={`shrink-0 rounded-full border px-2 py-0.5 text-xs font-medium ${
        progress === "solved" ? "border-success text-success" : "border-field text-muted"
      }`}
    >
      {PROGRESS_LABELS[progress]}
    </span>
  );
}
