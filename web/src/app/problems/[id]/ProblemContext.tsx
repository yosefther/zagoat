"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import { ApiError, request } from "@/lib/api";
import { useSession } from "@/lib/session";
import type { ProblemDetail } from "@/lib/types";

type ProblemState = {
  problem: ProblemDetail | null;
  error: string | null;
  refresh: () => Promise<void>;
};

const ProblemContext = createContext<ProblemState | null>(null);

/** Loads the signed-in view of one problem (lock, draft, progress, unlocks, usage) once. */
export function ProblemProvider({ problemId, children }: { problemId: string; children: ReactNode }) {
  const session = useSession();
  const [problem, setProblem] = useState<ProblemDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    () => request<ProblemDetail>(`/problems/${encodeURIComponent(problemId)}`),
    [problemId],
  );

  const refresh = useCallback(async () => {
    try {
      setProblem(await load());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    }
  }, [load]);

  useEffect(() => {
    if (session.status === "loading") return;
    let active = true;
    load()
      .then((data) => active && setProblem(data))
      .catch((err) => active && setError(err instanceof ApiError ? err.message : String(err)));
    return () => {
      active = false;
    };
  }, [load, session.status]);

  return (
    <ProblemContext.Provider value={{ problem, error, refresh }}>{children}</ProblemContext.Provider>
  );
}

export function useProblem(): ProblemState {
  const value = useContext(ProblemContext);
  if (!value) throw new Error("useProblem must be used inside <ProblemProvider>");
  return value;
}
