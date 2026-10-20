"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ResultsPanel } from "@/components/results/ResultsPanel";
import { ApiError, request } from "@/lib/api";
import { formatDuration, formatLocalDateTime } from "@/lib/format";
import { useSession } from "@/lib/session";
import type { HistoryItem, Job, ProblemSummary } from "@/lib/types";
import { VERDICT_LABELS, verdictTone } from "@/lib/verdicts";

export function HistoryList() {
  const session = useSession();
  const router = useRouter();
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [titles, setTitles] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (session.status === "signed_out") router.replace("/signin?return_to=%2Fhistory");
    if (session.status !== "signed_in") return;
    let active = true;
    Promise.all([request<HistoryItem[]>("/submissions"), request<ProblemSummary[]>("/problems")])
      .then(([history, problems]) => {
        if (!active) return;
        setItems(history);
        setTitles(Object.fromEntries(problems.map((p) => [p.id, p.title])));
      })
      .catch((err) => active && setError(err instanceof ApiError ? err.message : String(err)));
    return () => {
      active = false;
    };
  }, [session.status, router]);

  if (error) {
    return (
      <p role="alert" className="text-danger">
        {error}
      </p>
    );
  }
  if (!items) return <p className="text-muted">Loading your submissions…</p>;
  if (items.length === 0) {
    return (
      <p className="text-muted">
        No submissions yet. <Link href="/tasks">Pick a task</Link> and submit a solution.
      </p>
    );
  }
  return (
    <div className="overflow-x-auto rounded-md bg-panel">
      <table className="w-full min-w-[40rem] border-collapse text-left text-sm">
        <thead className="text-muted">
          <tr className="border-b border-line">
            <th scope="col" className="px-4 py-2 font-medium">Verdict</th>
            <th scope="col" className="py-2 pr-3 font-medium">Task</th>
            <th scope="col" className="py-2 pr-3 font-medium">Submitted</th>
            <th scope="col" className="py-2 pr-3 font-medium">Tests</th>
            <th scope="col" className="py-2 pr-3 font-medium">Timer</th>
            <th scope="col" className="py-2 pr-4 text-right font-medium">Version</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <HistoryRow key={item.job_id} item={item} title={titles[item.problem_id] ?? item.problem_id} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

const TONE_TEXT = { success: "text-success", danger: "text-danger", muted: "text-muted" };

function HistoryRow({ item, title }: { item: HistoryItem; title: string }) {
  const [job, setJob] = useState<Job | null>(null);
  const [open, setOpen] = useState(false);
  const tone = item.verdict ? verdictTone(item.verdict) : "muted";

  async function toggle() {
    setOpen(!open);
    if (!job) setJob(await request<Job>(`/jobs/${item.job_id}`));
  }

  return (
    <>
      <tr className="border-b border-line hover:bg-raised">
        <td className="px-4 py-2.5">
          <button
            type="button"
            aria-expanded={open}
            onClick={toggle}
            className={`rounded-sm font-medium ${TONE_TEXT[tone]}`}
          >
            <span aria-hidden="true" className="mr-1.5 inline-block w-2 text-muted">
              {open ? "▾" : "▸"}
            </span>
            {item.verdict ? VERDICT_LABELS[item.verdict] : "In progress"}
          </button>
        </td>
        <td className="py-2.5 pr-3">
          <Link href={`/tasks/${item.problem_id}`} className="text-ink">
            {title}
          </Link>
        </td>
        <td className="py-2.5 pr-3 text-muted">{formatLocalDateTime(item.created_at)}</td>
        <td className="py-2.5 pr-3 text-muted">
          {item.tests_total ? `${item.tests_passed}/${item.tests_total}` : "—"}
        </td>
        <td className="py-2.5 pr-3 font-mono text-xs text-muted">
          {item.timer_seconds !== null ? formatDuration(item.timer_seconds) : "—"}
        </td>
        <td className="py-2.5 pr-4 text-right text-muted">v{item.problem_version}</td>
      </tr>
      {open && (
        <tr className="border-b border-line">
          <td colSpan={6} className="px-4 pb-4">
            {job ? (
              <div className="flex flex-col gap-3">
                <ResultsPanel job={job} error={null} />
                <details className="rounded-md bg-raised">
                  <summary className="cursor-pointer px-3 py-2 text-sm text-muted">
                    Code you submitted
                  </summary>
                  {Object.entries(job.files).map(([name, code]) => (
                    <figure key={name} className="border-t border-line">
                      <figcaption className="px-3 py-1.5 font-mono text-xs text-muted">{name}</figcaption>
                      <pre className="max-h-80 overflow-auto px-3 pb-3 font-mono text-xs">
                        <code>{code}</code>
                      </pre>
                    </figure>
                  ))}
                </details>
              </div>
            ) : (
              <p className="py-2 text-sm text-muted">Loading…</p>
            )}
          </td>
        </tr>
      )}
    </>
  );
}
