export const CATEGORY_LABELS: Record<string, string> = {
  rag: "RAG",
  training: "Training",
  evals: "Evals",
  serving: "Serving",
};

export const DIFFICULTY_LABELS = {
  easy: "Easy",
  medium: "Medium",
  hard: "Hard",
} as const;

export const PROGRESS_LABELS = {
  not_started: "Not started",
  in_progress: "In progress",
  attempted: "Attempted",
  solved: "Solved",
} as const;
