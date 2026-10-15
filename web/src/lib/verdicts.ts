import type { Verdict } from "@/lib/types";

export const VERDICT_LABELS: Record<Verdict, string> = {
  passed: "Passed",
  failed: "Failed",
  error: "Error",
  time_limit: "Time limit exceeded",
  memory_limit: "Memory limit exceeded",
  system_error: "System error",
};

export function verdictTone(verdict: Verdict): "success" | "danger" | "muted" {
  if (verdict === "passed") return "success";
  if (verdict === "system_error") return "muted";
  return "danger";
}

export function formatMetric(value: number | null): string {
  if (value === null) return "not recorded";
  return Number.isInteger(value) ? String(value) : value.toFixed(3);
}
