import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { ProblemProvider } from "./ProblemContext";
import { Workspace } from "./Workspace";
import { Markdown } from "@/components/Markdown";
import { serverRequest } from "@/lib/api";
import type { ProblemDetail, ProblemSummary } from "@/lib/types";

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
    <Suspense fallback={<p className="p-6 text-muted">Loading problem…</p>}>
      <ProblemView params={params} />
    </Suspense>
  );
}

async function ProblemView({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [problem, list] = await Promise.all([
    loadProblem(id),
    serverRequest<ProblemSummary[]>("/problems").catch(() => null),
  ]);
  if (!problem) notFound();

  const ids = (list ?? []).map((p) => p.id);
  const index = ids.indexOf(problem.id);
  const neighbors = {
    previous: index > 0 ? ids[index - 1] : null,
    next: index >= 0 && index < ids.length - 1 ? ids[index + 1] : null,
  };

  return (
    <ProblemProvider problemId={problem.id}>
      <Workspace
        publicProblem={problem}
        neighbors={neighbors}
        statement={<Markdown>{problem.statement}</Markdown>}
      />
    </ProblemProvider>
  );
}
