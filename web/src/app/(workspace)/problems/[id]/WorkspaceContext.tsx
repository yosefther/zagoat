"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { useProblem } from "./ProblemContext";
import { ApiError, request } from "@/lib/api";
import type { Files } from "@/lib/autosave";
import { pollJob } from "@/lib/jobs";
import type { Job } from "@/lib/types";
import { useTimer } from "@/lib/useTimer";

export type Kind = "run" | "submit";
type JobState = { job: Job | null; error: string | null };

type WorkspaceValue = {
  canSolve: boolean;
  busy: Kind | null;
  run: JobState;
  submit: JobState;
  consoleTab: "sample" | "results";
  setConsoleTab: (tab: "sample" | "results") => void;
  start: (kind: Kind) => void;
  onFilesChange: (files: Files) => void;
  timer: ReturnType<typeof useTimer>;
  submitsLeft: number | null;
};

const WorkspaceContext = createContext<WorkspaceValue | null>(null);
const EMPTY: JobState = { job: null, error: null };

/** Run and Submit, the timer and the shortcuts, shared by the top bar, editor and console. */
export function WorkspaceProvider({ problemId, children }: { problemId: string; children: ReactNode }) {
  const { problem, refresh } = useProblem();
  const timer = useTimer(problemId);
  const files = useRef<Files>({});
  const polling = useRef<AbortController | null>(null);
  const [busy, setBusy] = useState<Kind | null>(null);
  const [run, setRun] = useState<JobState>(EMPTY);
  const [submit, setSubmit] = useState<JobState>(EMPTY);
  const [consoleTab, setConsoleTab] = useState<"sample" | "results">("sample");

  const canSolve = Boolean(problem && problem.lock === null && !problem.read_only);
  const usage = problem?.usage;
  const submitsLeft = usage ? Math.max(0, usage.submits_limit - usage.submits_used) : null;

  useEffect(() => () => polling.current?.abort(), []);

  const onFilesChange = useCallback((next: Files) => {
    files.current = next;
  }, []);

  // Set synchronously in `start`, so two key presses in one tick can't start two jobs.
  const busyRef = useRef<Kind | null>(null);
  const timerRef = useRef(timer);
  useEffect(() => {
    timerRef.current = timer;
  }, [timer]);

  const start = useCallback(
    async (kind: Kind) => {
      if (!canSolve || busyRef.current) return;
      if (kind === "submit" && submitsLeft === 0) return;
      const set = kind === "run" ? setRun : setSubmit;
      polling.current?.abort();
      const controller = new AbortController();
      polling.current = controller;
      busyRef.current = kind;
      setBusy(kind);
      setConsoleTab(kind === "run" ? "sample" : "results");
      set(EMPTY);
      try {
        const elapsed = timerRef.current.elapsedSeconds;
        const body =
          kind === "submit" && elapsed !== null
            ? { files: files.current, timer_seconds: elapsed }
            : { files: files.current };
        const { job_id } = await request<{ job_id: string }>(
          `/problems/${encodeURIComponent(problemId)}/${kind === "run" ? "runs" : "submissions"}`,
          { method: "POST", body },
        );
        const finished = await pollJob(job_id, (job) => set({ job, error: null }), controller.signal);
        if (finished.kind === "submit" && finished.verdict === "passed") timerRef.current.stop();
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        set({ job: null, error: err instanceof ApiError || err instanceof Error ? err.message : String(err) });
      } finally {
        if (polling.current === controller) {
          busyRef.current = null;
          setBusy(null);
        }
        // Progress, unlocks and remaining Submits may have changed.
        void refresh();
      }
    },
    [canSolve, problemId, refresh, submitsLeft],
  );

  // Ctrl/Cmd+Enter runs, Ctrl/Cmd+Shift+Enter submits (the editor registers the same keys).
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Enter" || !(event.ctrlKey || event.metaKey)) return;
      // Inside the editor, Monaco's own commands handle these keys.
      if (event.target instanceof Element && event.target.closest(".monaco-editor")) return;
      event.preventDefault();
      void start(event.shiftKey ? "submit" : "run");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [start]);

  const value = useMemo<WorkspaceValue>(
    () => ({
      canSolve,
      busy,
      run,
      submit,
      consoleTab,
      setConsoleTab,
      start: (kind) => void start(kind),
      onFilesChange,
      timer,
      submitsLeft,
    }),
    [canSolve, busy, run, submit, consoleTab, start, onFilesChange, timer, submitsLeft],
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace(): WorkspaceValue {
  const value = useContext(WorkspaceContext);
  if (!value) throw new Error("useWorkspace must be used inside <WorkspaceProvider>");
  return value;
}
