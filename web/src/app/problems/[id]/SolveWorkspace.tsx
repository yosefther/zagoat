"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { useProblem } from "@/app/problems/[id]/ProblemContext";
import { SolveArea } from "@/app/problems/[id]/SolveArea";
import { ResultsPanel } from "@/components/results/ResultsPanel";
import { ApiError, request } from "@/lib/api";
import type { Files } from "@/lib/autosave";
import { formatDuration, formatLocalTime } from "@/lib/format";
import { pollJob } from "@/lib/jobs";
import type { Job, ProblemDetail } from "@/lib/types";
import { useTimer } from "@/lib/useTimer";

/** Editor on top; results, limits, the timer and the Run and Submit buttons below. */
export function SolveWorkspace({ problem }: { problem: ProblemDetail }) {
  const { refresh } = useProblem();
  const timer = useTimer(problem.id);
  const files = useRef<Files>({});
  const polling = useRef<AbortController | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<"run" | "submit" | null>(null);

  useEffect(() => () => polling.current?.abort(), []);

  const onFilesChange = useCallback((next: Files) => {
    files.current = next;
  }, []);

  async function start(kind: "run" | "submit") {
    polling.current?.abort();
    const controller = new AbortController();
    polling.current = controller;
    setBusy(kind);
    setError(null);
    setJob(null);
    try {
      const path = kind === "run" ? "runs" : "submissions";
      const body =
        kind === "submit" && timer.elapsedSeconds !== null
          ? { files: files.current, timer_seconds: timer.elapsedSeconds }
          : { files: files.current };
      const { job_id } = await request<{ job_id: string }>(
        `/problems/${encodeURIComponent(problem.id)}/${path}`,
        { method: "POST", body },
      );
      const finished = await pollJob(job_id, setJob, controller.signal);
      if (finished.kind === "submit" && finished.verdict === "passed") timer.stop();
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setError(err instanceof ApiError || err instanceof Error ? err.message : String(err));
    } finally {
      if (polling.current === controller) setBusy(null);
      // Progress, unlocks and remaining Submits may have changed.
      void refresh();
    }
  }

  const usage = problem.usage;
  const submitsLeft = usage ? Math.max(0, usage.submits_limit - usage.submits_used) : null;
  const outOfSubmits = submitsLeft === 0;

  return (
    <div className="grid min-h-0 flex-1 grid-rows-[minmax(0,3fr)_minmax(0,2fr)]">
      <SolveArea problem={problem} onFilesChange={onFilesChange} />
      <div className="flex min-h-0 flex-col border-t border-border bg-bg">
        <ResultsPanel job={job} error={error} />
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-4 py-3">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted">
            {usage && (
              <span>
                {submitsLeft} of {usage.submits_limit} Submits left today · resets at{" "}
                {formatLocalTime(usage.submits_reset_at)}
                {outOfSubmits && problem.plan === "free" && (
                  <>
                    {" · "}
                    <Link href="/pricing">Upgrade for more</Link>
                  </>
                )}
              </span>
            )}
            <label className="inline-flex items-center gap-2">
              <input
                type="checkbox"
                className="size-4 accent-[var(--ink)]"
                checked={timer.running}
                onChange={(event) => (event.target.checked ? timer.start() : timer.stop())}
              />
              Timer
              {timer.elapsedSeconds !== null && (
                <span className="font-mono text-ink" aria-live="off">
                  {formatDuration(timer.elapsedSeconds)}
                </span>
              )}
            </label>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="btn-secondary"
              disabled={busy !== null}
              onClick={() => start("run")}
            >
              {busy === "run" ? "Running…" : "Run tests"}
            </button>
            <button
              type="button"
              className="btn-primary"
              disabled={busy !== null || outOfSubmits}
              onClick={() => start("submit")}
            >
              {busy === "submit" ? "Submitting…" : "Submit solution"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
