/**
 * Read-only previews of real tasks for the landing page. Titles and ids must match
 * problems/<id>/problem.yaml (samples.test.ts checks this).
 */

export type SampleTask = {
  id: string;
  category: "rag" | "training" | "evals" | "serving";
  difficulty: "easy" | "medium" | "hard";
  minutes: number;
  title: string;
  brief: string;
  file: string;
  code: string;
  /** Plain-words names of some hidden tests; the names are shown in results anyway. */
  checks: string[];
  /** The metric Submit measures, and roughly where the starter code lands. */
  metric?: { label: string; threshold: number; starter: number };
};

export const SAMPLE_TASKS: SampleTask[] = [
  {
    id: "rag-chunking-01",
    category: "rag",
    difficulty: "medium",
    minutes: 45,
    title: "Fix the chunking in a RAG pipeline",
    brief:
      "A support bot keeps citing the wrong policy. Find out why retrieval misses, fix how " +
      "handbook pages are chunked, and get recall@5 to 0.80 or more.",
    file: "chunker.py",
    code: `def chunk_document(doc, markdown, max_words=40):
    words = markdown.split()
    for start in range(0, len(words) - max_words, max_words):
        window = words[start : start + max_words]
        ...  # headings land in the wrong chunk`,
    checks: [
      "Every handbook section is indexed",
      "Chunks start with their heading",
      "No text is dropped or mixed between sections",
      "The prompt carries the retrieved evidence",
    ],
    metric: { label: "recall@5", threshold: 0.8, starter: 0.4 },
  },
  {
    id: "evals-ticket-classifier-01",
    category: "evals",
    difficulty: "easy",
    minutes: 30,
    title: "Write an eval for a ticket classifier",
    brief:
      "An LLM labels support tickets and nobody knows how well. Parse its messy replies and " +
      "report per-label precision, recall and F1.",
    file: "eval.py",
    code: `def parse_label(reply: str) -> str | None:
    """'Label: Bug.' -> 'bug'; hedged answers -> None."""
    raise NotImplementedError`,
    checks: [
      "Hedged or malformed replies parse to None",
      "Unparseable replies count as wrong",
      "Macro F1 averages every label, even unseen ones",
      "The model is asked once per ticket",
    ],
  },
];
