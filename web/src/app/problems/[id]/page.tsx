import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { ProblemProvider } from "@/app/problems/[id]/ProblemContext";
import { ProblemExtras } from "@/app/problems/[id]/ProblemExtras";
import { ProblemWorkspace } from "@/app/problems/[id]/ProblemWorkspace";
import { Markdown } from "@/components/Markdown";
import { ProblemMeta } from "@/components/ProblemMeta";
import { serverRequest } from "@/lib/api";
import type { ProblemDetail } from "@/lib/types";

async function loadProblem(id: string): Promise<ProblemDetail | null> {
  return serverRequest<ProblemDetail>(`/problems/${encodeURIComponent(id)}`);
}

export async function generateMetadata({
  params,
}: PageProps<"/problems/[id]">): Promise<Metadata> {
  const { id } = await params;
  const problem = await loadProblem(id).catch(() => null);
  return problem
    ? { title: problem.title, description: problem.summary }
    : { title: "Problem not found" };
}

export default function ProblemPage({ params }: PageProps<"/problems/[id]">) {
  return (
    <Suspense
      fallback={
        <main className="container-page py-12">
          <p className="text-muted">Loading problem…</p>
        </main>
      }
    >
      <ProblemView params={params} />
    </Suspense>
  );
}

async function ProblemView({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const problem = await loadProblem(id);
  if (!problem) notFound();

  return (
    <ProblemProvider problemId={problem.id}>
      <main className="flex flex-1 flex-col lg:grid lg:h-[calc(100dvh-4rem)] lg:flex-none lg:grid-cols-[minmax(22rem,2fr)_3fr]">
        <article className="flex min-w-0 flex-col gap-4 overflow-y-auto border-border px-4 py-8 sm:px-6 lg:border-r">
          <ProblemMeta problem={problem} />
          <h1 className="text-2xl font-bold">{problem.title}</h1>
          <p className="rounded-lg border border-border bg-code p-3 text-sm lg:hidden">
            Solving works on desktop. Open this page on a larger screen to write and run code.
          </p>
          <Markdown className="max-w-prose">{problem.statement}</Markdown>
          <ProblemExtras />
        </article>
        <section aria-label="Workspace" className="hidden min-h-0 min-w-0 flex-col lg:flex">
          <ProblemWorkspace />
        </section>
      </main>
    </ProblemProvider>
  );
}
