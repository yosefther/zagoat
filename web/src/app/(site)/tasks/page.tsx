import type { Metadata } from "next";
import { Suspense } from "react";

import { PathGrid } from "./PathGrid";
import { TasksNav } from "@/components/TasksNav";
import { serverRequest } from "@/lib/api";
import type { LearningPath } from "@/lib/types";

export const metadata: Metadata = {
  title: "Tasks",
  description:
    "Pick a path through realistic AI engineering tasks: retrieval and RAG, evaluation and more.",
};

export default function TasksPage() {
  return (
    <main className="container-page flex flex-col gap-6 py-10">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl">Tasks</h1>
        <p className="max-w-[60ch] text-muted">
          A path is a short run of tasks on one theme, easier ones first. Start at the
          beginning, or open any task directly.
        </p>
      </div>
      <TasksNav current="paths" />
      <Suspense fallback={<p className="text-muted">Loading paths…</p>}>
        <Paths />
      </Suspense>
    </main>
  );
}

async function Paths() {
  const paths = await serverRequest<LearningPath[]>("/paths").catch(() => null);
  if (paths === null) {
    return (
      <p role="alert" className="text-danger">
        We couldn&apos;t load the paths. Reload the page in a minute.
      </p>
    );
  }
  if (paths.length === 0) {
    return <p className="text-muted">No paths yet. Browse all tasks instead.</p>;
  }
  return <PathGrid initial={paths} />;
}
