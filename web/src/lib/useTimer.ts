"use client";

import { useCallback, useEffect, useState } from "react";

/**
 * Optional timer for a problem (brief, section 2). The start time lives in localStorage so
 * a reload doesn't reset it. It only records time to Submit; it never affects grading.
 */
export function useTimer(problemId: string) {
  const key = `zagoat-timer:${problemId}`;
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    let saved: string | null = null;
    try {
      saved = localStorage.getItem(key);
    } catch {
      // Storage blocked: the timer still works for this page view.
    }
    const value = saved ? Number(saved) : null;
    if (value && Number.isFinite(value)) {
      // Restoring a saved timer after mount keeps server and client markup identical.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setStartedAt(value);
    }
  }, [key]);

  useEffect(() => {
    if (startedAt === null) return;
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, [startedAt]);

  const start = useCallback(() => {
    const value = Date.now();
    setStartedAt(value);
    setNow(value);
    try {
      localStorage.setItem(key, String(value));
    } catch {}
  }, [key]);

  const stop = useCallback(() => {
    setStartedAt(null);
    try {
      localStorage.removeItem(key);
    } catch {}
  }, [key]);

  const elapsedSeconds = startedAt === null ? null : Math.max(0, Math.floor((now - startedAt) / 1000));
  return { running: startedAt !== null, elapsedSeconds, start, stop };
}
