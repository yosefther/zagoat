import type { Metadata } from "next";

import { HistoryList } from "@/app/history/HistoryList";

export const metadata: Metadata = { title: "Submission history" };

export default function HistoryPage() {
  return (
    <main className="container-page flex flex-col gap-6 py-12">
      <h1 className="text-3xl font-bold">Submission history</h1>
      <HistoryList />
    </main>
  );
}
