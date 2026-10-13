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
};
