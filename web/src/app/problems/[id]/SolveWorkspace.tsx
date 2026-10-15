"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { SolveArea } from "@/app/problems/[id]/SolveArea";
import { ResultsPanel } from "@/components/results/ResultsPanel";
import { ApiError, request } from "@/lib/api";
import type { Files } from "@/lib/autosave";
import { pollJob } from "@/lib/jobs";
import type { Job, ProblemDetail } from "@/lib/types";

/** Editor on top; results and the Run and Submit buttons below. */
export function SolveWorkspace({ problem }: { problem: ProblemDetail }) {
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
      const { job_id } = await request<{ job_id: string }>(
        `/problems/${encodeURIComponent(problem.id)}/${path}`,
        { method: "POST", body: { files: files.current } },
      );
      await pollJob(job_id, setJob, controller.signal);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setError(err instanceof ApiError || err instanceof Error ? err.message : String(err));
    } finally {
      if (polling.current === controller) setBusy(null);
    }
  }

  return (
    <div className="grid min-h-0 flex-1 grid-rows-[minmax(0,3fr)_minmax(0,2fr)]">
      <SolveArea problem={problem} onFilesChange={onFilesChange} />
      <div className="flex min-h-0 flex-col border-t border-border bg-bg">
        <ResultsPanel job={job} error={error} />
        <div className="flex items-center justify-end gap-3 border-t border-border px-4 py-3">
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
            disabled={busy !== null}
            onClick={() => start("submit")}
          >
            {busy === "submit" ? "Submitting…" : "Submit solution"}
          </button>
        </div>
      </div>
    </div>
  );
}
