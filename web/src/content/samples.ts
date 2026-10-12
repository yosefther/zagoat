/** Read-only task previews for the landing page. All original; not real interview questions. */

export type SampleTask = {
  category: string;
  difficulty: "easy" | "medium" | "hard";
  minutes: number;
  title: string;
  brief: string;
  file: string;
  code: string;
};

export const SAMPLE_TASKS: SampleTask[] = [
  {
    category: "RAG",
    difficulty: "medium",
    minutes: 45,
    title: "Fix the chunking in a RAG pipeline",
    brief:
      "Answers about the refund policy keep citing the wrong section. Find out why " +
      "retrieval misses, fix the chunker, and get recall@5 above 0.80.",
    file: "chunker.py",
    code: `def chunk(doc: str, size: int = 512) -> list[str]:
    words = doc.split()
    return [
        " ".join(words[i : i + size])
        for i in range(0, len(words), size)
    ]  # headings end up glued to the wrong chunk`,
  },
  {
    category: "Evals",
    difficulty: "easy",
    minutes: 30,
    title: "Write an eval for a ticket classifier",
    brief:
      "A support-ticket classifier ships next week. Write an eval that reports per-label " +
      "precision and recall, and flags labels the model never predicts.",
    file: "eval.py",
    code: `def evaluate(model, dataset) -> dict[str, float]:
    preds = [model.predict(row.text) for row in dataset]
    # TODO: per-label precision and recall
    raise NotImplementedError`,
  },
  {
    category: "Training",
    difficulty: "hard",
    minutes: 60,
    title: "Find out why validation loss is flat",
    brief:
      "Training loss falls, but validation loss hasn't moved in 20 epochs. Find the bug in " +
      "the training loop and get validation accuracy over the target.",
    file: "train.py",
    code: `for epoch in range(epochs):
    model.eval()
    for x, y in train_loader:
        loss = loss_fn(model(x), y)
        loss.backward()
        optimizer.step()`,
  },
];
