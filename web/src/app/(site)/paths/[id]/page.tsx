import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { PathDetail } from "./PathDetail";
import { serverRequest } from "@/lib/api";
import type { LearningPath } from "@/lib/types";

async function loadPath(id: string): Promise<LearningPath | null> {
  return serverRequest<LearningPath>(`/paths/${encodeURIComponent(id)}`);
}

export async function generateMetadata({ params }: PageProps<"/paths/[id]">): Promise<Metadata> {
  const { id } = await params;
  const path = await loadPath(id).catch(() => null);
  return path ? { title: path.title, description: path.summary } : { title: "Path not found" };
}

export default function PathPage({ params }: PageProps<"/paths/[id]">) {
  return (
    <main className="container-page flex flex-col gap-8 py-10">
      <Suspense fallback={<p className="text-muted">Loading path…</p>}>
        <PathView params={params} />
      </Suspense>
    </main>
  );
}

async function PathView({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const path = await loadPath(id);
  if (!path) notFound();
  return <PathDetail initial={path} />;
}
