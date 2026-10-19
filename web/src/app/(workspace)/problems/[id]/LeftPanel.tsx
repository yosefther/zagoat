"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { useProblem } from "./ProblemContext";
import { Markdown } from "@/components/Markdown";
import { ProblemMeta } from "@/components/ProblemMeta";
import { ResultsPanel } from "@/components/results/ResultsPanel";
import { Tabs, panelId, tabId } from "@/components/Tabs";
import { ApiError, request } from "@/lib/api";
import { formatDuration, formatLocalDateTime } from "@/lib/format";
import type { HistoryItem, Job, ProblemDetail } from "@/lib/types";
import { VERDICT_LABELS, verdictTone } from "@/lib/verdicts";

const TABS_ID = "problem";
const TONE_TEXT = { success: "text-success", danger: "text-danger", muted: "text-muted" };
const TABS = [
  { id: "description", label: "Description" },
  { id: "hints", label: "Hints" },
  { id: "walkthrough", label: "Walkthrough" },
  { id: "submissions", label: "Submissions" },
];

type Props = {
  publicProblem: ProblemDetail;
  statement: ReactNode;
};

/** Left pane: the task and everything that unlocks around it. */
export function LeftPanel({ publicProblem, statement }: Props) {
  const [tab, setTab] = useState("description");
  const { problem } = useProblem();

  return (
    <div className="flex h-full min-h-0 flex-col bg-panel">
      <div className="border-b border-line">
        <Tabs tabs={TABS} active={tab} onSelect={setTab} idPrefix={TABS_ID} label="Problem" />
      </div>
      <div
        id={panelId(TABS_ID)}
        role="tabpanel"
        aria-labelledby={tabId(TABS_ID, tab)}
        className="min-h-0 flex-1 overflow-y-auto px-5 py-5"
      >
        {/* The statement stays mounted so it's in the server HTML and keeps its scroll. */}
        <div hidden={tab !== "description"}>
          <Description problem={publicProblem} statement={statement} />
        </div>
        {tab === "hints" && <Hints problem={problem} />}
        {tab === "walkthrough" && <Walkthrough problem={problem} />}
        {tab === "submissions" && <Submissions problem={problem} />}
      </div>
    </div>
  );
}

export function Description({ problem, statement }: { problem: ProblemDetail; statement: ReactNode }) {
  const samples = Object.entries(problem.sample_tests);
  return (
    <article className="flex max-w-[var(--measure)] flex-col gap-4">
      <ProblemMeta problem={problem} />
      <h1 className="text-xl font-bold">{problem.title}</h1>
      {statement}
      {samples.length > 0 && (
        <section className="flex flex-col gap-2">
          <h2 className="text-lg font-bold">Sample tests</h2>
          <p className="text-sm text-muted">
            Run tests runs these. Submit runs a larger hidden set.
          </p>
          {samples.map(([name, code]) => (
            <details key={name} className="rounded-md bg-raised">
              <summary className="cursor-pointer px-3 py-2 font-mono text-xs text-muted">
                {name}
              </summary>
              <pre className="overflow-x-auto border-t border-line p-3 font-mono text-xs leading-relaxed">
                <code>{code}</code>
              </pre>
            </details>
          ))}
        </section>
      )}
    </article>
  );
}

function SignInPrompt({ what }: { what: string }) {
  const pathname = usePathname();
  const params = new URLSearchParams({ return_to: pathname });
  return (
    <p className="text-sm text-muted">
      <Link href={`/signin?${params}`}>Sign in</Link> to see {what}.
    </p>
  );
}

function Upgrade({ children }: { children: ReactNode }) {
  return (
    <p className="text-sm text-muted">
      {children} <Link href="/pricing">See plans</Link>
    </p>
  );
}

function ErrorText({ message }: { message: string | null }) {
  return message ? (
    <p role="alert" className="text-sm text-danger">
      {message}
    </p>
  ) : null;
}

function Hints({ problem }: { problem: ProblemDetail | null }) {
  const { refresh } = useProblem();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  if (!problem) return <p className="text-sm text-muted">Loading…</p>;
  if (problem.lock === "sign_in") return <SignInPrompt what="hints" />;
  if (problem.hint_count === 0) return <p className="text-sm text-muted">This task has no hints.</p>;
  if (problem.lock === "paid") {
    return <Upgrade>Hints for this task are part of Lifetime and Pro.</Upgrade>;
  }
  const next = problem.hints.length + 1;

  async function reveal() {
    setLoading(true);
    setError(null);
    try {
      await request(`/problems/${encodeURIComponent(problem!.id)}/hints/${next}`, { method: "POST" });
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load the hint. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex max-w-[var(--measure)] flex-col gap-4">
      <p className="text-sm text-muted">
        Hints open one at a time and never affect your result.
      </p>
      {problem.hints.map((hint, index) => (
        <section key={index} className="flex flex-col gap-2 border-l-2 border-brand pl-4">
          <h2 className="text-base font-bold">Hint {index + 1}</h2>
          <Markdown className="text-sm">{hint}</Markdown>
        </section>
      ))}
      {next <= problem.hint_count && !problem.read_only && (
        <button type="button" className="btn-secondary self-start" disabled={loading} onClick={reveal}>
          {loading ? "Loading…" : `Show hint ${next} of ${problem.hint_count}`}
        </button>
      )}
      <ErrorText message={error} />
    </div>
  );
}

function Walkthrough({ problem }: { problem: ProblemDetail | null }) {
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  if (!problem) return <p className="text-sm text-muted">Loading…</p>;
  if (!problem.has_walkthrough) {
    return <p className="text-sm text-muted">This task doesn&apos;t have a walkthrough yet.</p>;
  }
  if (problem.lock === "sign_in") return <SignInPrompt what="the walkthrough" />;
  if (!problem.walkthrough_unlocked) {
    return <Upgrade>The full written walkthrough is part of Lifetime and Pro.</Upgrade>;
  }

  async function load() {
    setError(null);
    try {
      const data = await request<{ markdown: string }>(
        `/problems/${encodeURIComponent(problem!.id)}/walkthrough`,
      );
      setMarkdown(data.markdown);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load the walkthrough.");
    }
  }

  if (markdown) return <Markdown className="max-w-[var(--measure)]">{markdown}</Markdown>;
  return (
    <div className="flex max-w-[var(--measure)] flex-col gap-3">
      <p className="text-sm text-muted">
        The walkthrough shows the full solution. Open it when you&apos;re ready to compare.
      </p>
      <button type="button" className="btn-secondary self-start" onClick={load}>
        Show the walkthrough
      </button>
      <ErrorText message={error} />
    </div>
  );
}

function Submissions({ problem }: { problem: ProblemDetail | null }) {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const signedIn = problem !== null && problem.lock !== "sign_in";
  const marker = `${problem?.usage?.submits_used}-${problem?.progress_detail?.state}`;

  useEffect(() => {
    if (!signedIn || !problem) return;
    let active = true;
    request<HistoryItem[]>(`/problems/${encodeURIComponent(problem.id)}/submissions`)
      .then((data) => active && setItems(data))
      .catch(() => active && setItems([]));
    return () => {
      active = false;
    };
    // Reload after each finished Submit (usage and progress change then).
  }, [signedIn, problem?.id, marker]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!problem) return <p className="text-sm text-muted">Loading…</p>;
  if (!signedIn) return <SignInPrompt what="your submissions" />;
  return (
    <div className="flex flex-col gap-6">
      <Reference problem={problem} />
      <section className="flex flex-col gap-2">
        <h2 className="text-base font-bold">Your submissions</h2>
        {items === null ? (
          <p className="text-sm text-muted">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-muted">
            Nothing submitted yet. Submit solution runs the hidden tests and saves the result here.
          </p>
        ) : (
          <ul className="flex flex-col">
            {items.map((item) => (
              <SubmissionRow key={item.job_id} item={item} />
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function SubmissionRow({ item }: { item: HistoryItem }) {
  const [open, setOpen] = useState(false);
  const [job, setJob] = useState<Job | null>(null);
  const tone = item.verdict ? verdictTone(item.verdict) : "muted";

  async function toggle() {
    setOpen(!open);
    if (!job) setJob(await request<Job>(`/jobs/${item.job_id}`));
  }

  return (
    <li className="border-b border-line last:border-b-0">
      <button
        type="button"
        aria-expanded={open}
        onClick={toggle}
        className="flex w-full flex-wrap items-baseline gap-x-3 gap-y-1 py-2.5 text-left text-sm hover:bg-raised"
      >
        <span className={`font-medium ${TONE_TEXT[tone]}`}>
          {item.verdict ? VERDICT_LABELS[item.verdict] : "In progress"}
        </span>
        <span className="text-muted">{formatLocalDateTime(item.created_at)}</span>
        {item.tests_total ? (
          <span className="text-muted">
            {item.tests_passed}/{item.tests_total} tests
          </span>
        ) : null}
        {item.timer_seconds !== null && (
          <span className="text-muted">{formatDuration(item.timer_seconds)}</span>
        )}
        <span className="ml-auto text-xs text-muted">v{item.problem_version}</span>
      </button>
      {open && (
        <div className="pb-3">
          {job ? <ResultsPanel job={job} error={null} /> : <p className="text-sm text-muted">Loading…</p>}
        </div>
      )}
    </li>
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

  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-base font-bold">Reference solution</h2>
      {!problem.reference_unlocked ? (
        <p className="text-sm text-muted">Unlocks after your first Submit on this task.</p>
      ) : files ? (
        Object.entries(files).map(([name, code]) => (
          <details key={name} open className="rounded-md bg-raised">
            <summary className="cursor-pointer px-3 py-2 font-mono text-xs text-muted">{name}</summary>
            <pre className="max-h-96 overflow-auto border-t border-line p-3 font-mono text-xs leading-relaxed">
              <code>{code}</code>
            </pre>
          </details>
        ))
      ) : (
        <button type="button" className="btn-secondary self-start" onClick={load}>
          Show the reference solution
        </button>
      )}
      <ErrorText message={error} />
    </section>
  );
}
