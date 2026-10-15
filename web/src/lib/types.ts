/** Shapes returned by the zagoat API. */

export type Me = {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  code_opt_in: boolean;
  created_at: string;
};

export type Access = "free" | "paid";

export type ProblemSummary = {
  id: string;
  title: string;
  summary: string;
  category: string;
  difficulty: "easy" | "medium" | "hard";
  est_minutes: number;
  access: Access;
  progress: "not_started" | "in_progress" | "attempted" | "solved" | null;
};

export type MetricSpec = {
  name: string;
  threshold: number;
  goal: "at_least" | "at_most";
};

export type ProblemDetail = ProblemSummary & {
  version: number;
  statement: string;
  metrics: MetricSpec[];
  hint_count: number;
  has_walkthrough: boolean;
  lock: "sign_in" | "paid" | null;
  starter_files: Record<string, string> | null;
  draft_files: Record<string, string> | null;
  draft_updated_at: string | null;
};

export type Verdict =
  | "passed"
  | "failed"
  | "error"
  | "time_limit"
  | "memory_limit"
  | "system_error";

export type TestResult = {
  name: string;
  outcome: "passed" | "failed" | "error" | "skipped";
  message: string | null;
};

export type MetricResult = {
  name: string;
  value: number | null;
  threshold: number | null;
  goal: "at_least" | "at_most" | null;
  met: boolean | null;
};

export type Job = {
  job_id: string;
  problem_id: string;
  problem_version: number;
  kind: "run" | "submit";
  status: "queued" | "running" | "done";
  verdict: Verdict | null;
  message: string | null;
  tests_passed: number | null;
  tests_total: number | null;
  tests: TestResult[];
  metrics: MetricResult[];
  stdout: string | null;
  stderr: string | null;
  duration_ms: number | null;
  created_at: string;
};
