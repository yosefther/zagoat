"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useProblem } from "@/app/problems/[id]/ProblemContext";
import { Markdown } from "@/components/Markdown";
import { ApiError, request } from "@/lib/api";
import { formatLocalDateTime } from "@/lib/format";
import type { HistoryItem, ProblemDetail } from "@/lib/types";
import { VERDICT_LABELS } from "@/lib/verdicts";

/** Hints, reference solution, walkthrough and recent submissions, under the statement. */
export function ProblemExtras() {
  const { problem } = useProblem();
  if (!problem || problem.lock === "sign_in") return null;
  return (
    <div className="flex max-w-prose flex-col gap-6 border-t border-border pt-6">
      <Hints problem={problem} />
      <Reference problem={problem} />
      <Walkthrough problem={problem} />
      <RecentSubmissions problem={problem} />
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-lg font-bold">{title}</h2>
      {children}
    </section>
  );
}

function ErrorText({ message }: { message: string | null }) {
  return message ? (
    <p role="alert" className="text-sm text-danger">
      {message}
    </p>
  ) : null;
}

function Hints({ problem }: { problem: ProblemDetail }) {
  const { refresh } = useProblem();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  if (problem.hint_count === 0) return null;
  if (problem.lock === "paid") {
    return (
      <Section title="Hints">
        <p className="text-sm text-muted">
          Hints for this problem are part of Lifetime and Pro. <Link href="/pricing">See plans</Link>
        </p>
      </Section>
    );
  }
  const next = problem.hints.length + 1;

  async function reveal() {
    setLoading(true);
    setError(null);
    try {
      await request(`/problems/${encodeURIComponent(problem.id)}/hints/${next}`, {
        method: "POST",
      });
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load the hint. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Section title="Hints">
      {problem.hints.map((hint, index) => (
        <div key={index} className="card p-4">
          <p className="mb-2 text-xs font-medium tracking-wide text-muted uppercase">
            Hint {index + 1}
          </p>
          <Markdown className="text-sm">{hint}</Markdown>
        </div>
      ))}
      {next <= problem.hint_count && !problem.read_only && (
        <button type="button" className="btn-secondary self-start" disabled={loading} onClick={reveal}>
          {loading ? "Loading…" : `Show hint ${next} of ${problem.hint_count}`}
        </button>
      )}
      <ErrorText message={error} />
    </Section>
  );
}

function Reference({ problem }: { problem: ProblemDetail }) {
  const [files, setFiles] = useState<Record<string, string> | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const data = await request<{ files: Record<string, string> }>(
        `/problems/${encodeURIComponent(problem.id)}/reference`,
      );
      setFiles(data.files);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load the reference solution.");
    }
  }

  if (!problem.reference_unlocked) {
    return (
      <Section title="Reference solution">
        <p className="text-sm text-muted">Unlocks after your first Submit on this problem.</p>
      </Section>
    );
  }
  return (
    <Section title="Reference solution">
      {files ? (
        Object.entries(files).map(([name, code]) => (
          <figure key={name} className="card overflow-hidden">
            <figcaption className="border-b border-border px-3 py-1.5 font-mono text-xs text-muted">
              {name}
            </figcaption>
            <pre className="max-h-96 overflow-auto p-3 font-mono text-xs">
              <code>{code}</code>
            </pre>
          </figure>
        ))
      ) : (
        <button type="button" className="btn-secondary self-start" onClick={load}>
          Show the reference solution
        </button>
      )}
      <ErrorText message={error} />
    </Section>
  );
}

function Walkthrough({ problem }: { problem: ProblemDetail }) {
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  if (!problem.has_walkthrough) return null;
  if (!problem.walkthrough_unlocked) {
    return (
      <Section title="Walkthrough">
        <p className="text-sm text-muted">
          A full written walkthrough is part of Lifetime and Pro.{" "}
          <Link href="/pricing">See plans</Link>
        </p>
      </Section>
    );
  }

  async function load() {
    setError(null);
    try {
      const data = await request<{ markdown: string }>(
        `/problems/${encodeURIComponent(problem.id)}/walkthrough`,
      );
      setMarkdown(data.markdown);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load the walkthrough.");
    }
  }

  return (
    <Section title="Walkthrough">
      {markdown ? (
        <Markdown className="text-sm">{markdown}</Markdown>
      ) : (
        <>
          <p className="text-sm text-muted">
            The walkthrough shows the full solution. Open it when you&apos;re ready.
          </p>
          <button type="button" className="btn-secondary self-start" onClick={load}>
            Show the walkthrough
          </button>
        </>
      )}
      <ErrorText message={error} />
    </Section>
  );
}

function RecentSubmissions({ problem }: { problem: ProblemDetail }) {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const submittedAt = problem.progress_detail?.first_submit_at;
  const state = problem.progress_detail?.state;

  useEffect(() => {
    if (!submittedAt) return;
    let active = true;
    request<HistoryItem[]>(`/problems/${encodeURIComponent(problem.id)}/submissions`)
      .then((data) => active && setItems(data.slice(0, 5)))
      .catch(() => active && setItems([]));
    return () => {
      active = false;
    };
    // Reload when progress changes, i.e. after each finished Submit.
  }, [problem.id, submittedAt, state, problem.usage?.submits_used]);

  if (!submittedAt || !items || items.length === 0) return null;
  return (
    <Section title="Your submissions">
      <ul className="flex flex-col gap-1 text-sm">
        {items.map((item) => (
          <li key={item.job_id} className="flex flex-wrap gap-x-3">
            <span className={item.verdict === "passed" ? "text-success" : "text-ink"}>
              {item.verdict ? VERDICT_LABELS[item.verdict] : "In progress"}
            </span>
            <span className="text-muted">{formatLocalDateTime(item.created_at)}</span>
            <span className="text-muted">version {item.problem_version}</span>
          </li>
        ))}
      </ul>
      <Link href="/history" className="self-start text-sm">
        See all your submissions
      </Link>
    </Section>
  );
}
