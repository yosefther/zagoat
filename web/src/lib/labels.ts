export const CATEGORY_LABELS: Record<string, string> = {
  rag: "RAG",
  training: "Training",
  evals: "Evals",
  serving: "Serving",
};

export const ACCESS_LABELS = {
  free: "Free",
  paid: "Lifetime and Pro",
} as const;

export const PROGRESS_LABELS = {
  not_started: "Not started",
  in_progress: "In progress",
  attempted: "Attempted",
  solved: "Solved",
} as const;
