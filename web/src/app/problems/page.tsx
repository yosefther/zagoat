import type { Metadata } from "next";
import { Suspense } from "react";

import { ProblemList } from "@/app/problems/ProblemList";

export const metadata: Metadata = {
  title: "Problems",
  description: "Realistic AI engineering tasks: RAG, training, evals and serving.",
};

export default function ProblemsPage() {
  return (
    <main className="container-page flex flex-col gap-8 py-12">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Problems</h1>
        <p className="max-w-prose text-muted">
          Each task is a realistic piece of AI engineering work in Python, 30 to 60 minutes
          long, graded by hidden tests and metrics.
        </p>
      </div>
      <Suspense fallback={<p className="text-muted">Loading problems…</p>}>
        <ProblemList />
      </Suspense>
    </main>
  );
}
