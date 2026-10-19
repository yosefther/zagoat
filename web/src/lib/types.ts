/** Shapes returned by the zagoat API. */

export type Usage = {
  submits_used: number;
  submits_limit: number;
  submits_reset_at: string;
  runs_used: number;
  runs_limit: number;
  runs_reset_at: string;
};

export type PlanName = "free" | "lifetime" | "pro_monthly" | "pro_yearly";

export type Me = {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  code_opt_in: boolean;
  created_at: string;
  plan: { tier: "free" | "paid"; name: PlanName; access_ends_at: string | null };
  usage: Usage;
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
  best_result: { value: number; label: string } | null;
};

export type MetricSpec = {
  name: string;
  threshold: number;
  goal: "at_least" | "at_most";
};

export type ProblemDetail = ProblemSummary & {
  version: number;
  statement: string;
  sample_tests: Record<string, string>;
  metrics: MetricSpec[];
  hint_count: number;
  has_walkthrough: boolean;
  lock: "sign_in" | "paid" | null;
  read_only: boolean;
  starter_files: Record<string, string> | null;
  draft_files: Record<string, string> | null;
  draft_updated_at: string | null;
  hints: string[];
  progress_detail: {
    state: string;
    hints_revealed: number;
    first_submit_at: string | null;
    solved_at: string | null;
    timer_seconds: number | null;
  } | null;
  reference_unlocked: boolean;
  walkthrough_unlocked: boolean;
  plan: PlanName | null;
  usage: Usage | null;
};

export type HistoryItem = {
  job_id: string;
  problem_id: string;
  problem_version: number;
  kind: "run" | "submit";
  status: "queued" | "running" | "done";
  verdict: Verdict | null;
  tests_passed: number | null;
  tests_total: number | null;
  metrics: MetricResult[];
  duration_ms: number | null;
  timer_seconds: number | null;
  created_at: string;
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
  timer_seconds: number | null;
  files: Record<string, string>;
  created_at: string;
};

export type Plans = {
  currency: string;
  lifetime_price_cents: number | null;
  lifetime_available: boolean;
  lifetime_remaining: number;
  pro_enabled: boolean;
  pro_monthly_price_cents: number;
  pro_yearly_price_cents: number;
  payments_enabled: boolean;
  current_plan: PlanName | null;
};
