import type { Metadata } from "next";
import { Suspense } from "react";

import { ProblemList } from "./ProblemList";

export const metadata: Metadata = {
  title: "Problems",
  description: "Realistic AI engineering tasks: RAG, training, evals and serving.",
};

export default function ProblemsPage() {
  return (
    <main className="container-page flex flex-col gap-6 py-10">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold">Problems</h1>
        <p className="max-w-[var(--measure)] text-muted">
          Realistic pieces of AI engineering work in Python, 30 to 60 minutes each, graded by
          hidden tests and metrics.
        </p>
      </div>
      <Suspense fallback={<p className="text-muted">Loading problems…</p>}>
        <ProblemList />
      </Suspense>
    </main>
  );
}
