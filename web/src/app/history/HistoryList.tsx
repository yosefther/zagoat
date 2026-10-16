"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ResultsPanel } from "@/components/results/ResultsPanel";
import { ApiError, request } from "@/lib/api";
import { formatDuration, formatLocalDateTime } from "@/lib/format";
import { useSession } from "@/lib/session";
import type { HistoryItem, Job, ProblemSummary } from "@/lib/types";
import { VERDICT_LABELS } from "@/lib/verdicts";

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
        No submissions yet. <Link href="/problems">Pick a problem</Link> and submit a solution.
      </p>
    );
  }
  return (
    <ul className="flex flex-col gap-3">
      {items.map((item) => (
        <HistoryRow key={item.job_id} item={item} title={titles[item.problem_id] ?? item.problem_id} />
      ))}
    </ul>
  );
}

function HistoryRow({ item, title }: { item: HistoryItem; title: string }) {
  const [job, setJob] = useState<Job | null>(null);
  const [open, setOpen] = useState(false);

  async function toggle() {
    setOpen(!open);
    if (!job) setJob(await request<Job>(`/jobs/${item.job_id}`));
  }

  return (
    <li className="card flex flex-col">
      <button
        type="button"
        aria-expanded={open}
        onClick={toggle}
        className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-xl p-4 text-left"
      >
        <span className={`font-medium ${item.verdict === "passed" ? "text-success" : ""}`}>
          {item.verdict ? VERDICT_LABELS[item.verdict] : "In progress"}
        </span>
        <span className="font-medium">{title}</span>
        <span className="text-sm text-muted">{formatLocalDateTime(item.created_at)}</span>
        {item.tests_total ? (
          <span className="text-sm text-muted">
            {item.tests_passed} of {item.tests_total} tests
          </span>
        ) : null}
        {item.timer_seconds !== null && (
          <span className="text-sm text-muted">Timer {formatDuration(item.timer_seconds)}</span>
        )}
        <span className="text-sm text-muted">version {item.problem_version}</span>
      </button>
      {open && (
        <div className="flex flex-col gap-3 border-t border-border p-4">
          {job ? (
            <>
              <ResultsPanel job={job} error={null} />
              <details>
                <summary className="cursor-pointer text-sm text-muted">Code you submitted</summary>
                {Object.entries(job.files).map(([name, code]) => (
                  <figure key={name} className="mt-2 overflow-hidden rounded-lg border border-border">
                    <figcaption className="border-b border-border px-3 py-1.5 font-mono text-xs text-muted">
                      {name}
                    </figcaption>
                    <pre className="max-h-80 overflow-auto bg-code p-3 font-mono text-xs">
                      <code>{code}</code>
                    </pre>
                  </figure>
                ))}
              </details>
              <Link href={`/problems/${item.problem_id}`} className="self-start text-sm">
                Open the problem
              </Link>
            </>
          ) : (
            <p className="text-sm text-muted">Loading…</p>
          )}
        </div>
      )}
    </li>
  );
}
