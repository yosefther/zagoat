import type { Metadata } from "next";
import { Suspense } from "react";

import { TaskList } from "./TaskList";
import { TasksNav } from "@/components/TasksNav";

export const metadata: Metadata = {
  title: "All tasks",
  description: "Every zagoat task: RAG, training, evals and serving.",
};

export default function AllTasksPage() {
  return (
    <main className="container-page flex flex-col gap-6 py-10">
      <h1 className="text-3xl">Tasks</h1>
      <TasksNav current="all" />
      <Suspense fallback={<p className="text-muted">Loading tasks…</p>}>
        <TaskList />
      </Suspense>
    </main>
  );
}
