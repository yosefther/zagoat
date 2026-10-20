import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { ProblemProvider } from "./ProblemContext";
import { Workspace } from "./Workspace";
import { Markdown } from "@/components/Markdown";
import { serverRequest } from "@/lib/api";
import type { LearningPath, ProblemDetail, ProblemSummary } from "@/lib/types";

async function loadProblem(id: string): Promise<ProblemDetail | null> {
  return serverRequest<ProblemDetail>(`/problems/${encodeURIComponent(id)}`);
}

export async function generateMetadata({
  params,
}: PageProps<"/tasks/[id]">): Promise<Metadata> {
  const { id } = await params;
  const problem = await loadProblem(id).catch(() => null);
  return problem
    ? { title: problem.title, description: problem.summary }
    : { title: "Task not found" };
}

export default function TaskPage({ params, searchParams }: PageProps<"/tasks/[id]">) {
  return (
    <Suspense fallback={<p className="p-6 text-muted">Loading task…</p>}>
      <TaskView params={params} searchParams={searchParams} />
    </Suspense>
  );
}

async function TaskView({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [{ id }, query] = await Promise.all([params, searchParams]);
  const pathId = typeof query.path === "string" ? query.path : null;
  const [problem, path, list] = await Promise.all([
    loadProblem(id),
    pathId
      ? serverRequest<LearningPath>(`/paths/${encodeURIComponent(pathId)}`).catch(() => null)
      : null,
    serverRequest<ProblemSummary[]>("/problems").catch(() => null),
  ]);
  if (!problem) notFound();

  // Arriving from a path, previous and next follow that path; otherwise the full list.
  const onPath = path?.tasks.some((task) => task.id === problem.id) ? path : null;
  const ids = (onPath?.tasks ?? list ?? []).map((task) => task.id);
  const index = ids.indexOf(problem.id);
  const suffix = onPath ? `?path=${onPath.id}` : "";
  const neighbors = {
    previous: index > 0 ? `/tasks/${ids[index - 1]}${suffix}` : null,
    next: index >= 0 && index < ids.length - 1 ? `/tasks/${ids[index + 1]}${suffix}` : null,
    back: onPath
      ? { href: `/paths/${onPath.id}`, label: onPath.title }
      : { href: "/tasks", label: "Tasks" },
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
