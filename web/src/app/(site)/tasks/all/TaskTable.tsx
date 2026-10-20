"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Difficulty, LockIcon, StatusIcon } from "@/components/ProblemBits";
import { request } from "@/lib/api";
import { CATEGORY_LABELS, DIFFICULTY_LABELS, PROGRESS_LABELS } from "@/lib/labels";
import { useSession } from "@/lib/session";
import type { ProblemSummary } from "@/lib/types";

type SortKey = "title" | "category" | "difficulty" | "est_minutes" | "best";
type Status = "all" | "solved" | "attempted" | "not_started";

const DIFFICULTY_RANK = { easy: 0, medium: 1, hard: 2 } as const;
const CATEGORY_ORDER = ["rag", "training", "evals", "serving"];

function statusOf(problem: ProblemSummary): Exclude<Status, "all"> {
  if (problem.progress === "solved") return "solved";
  if (problem.progress === "attempted" || problem.progress === "in_progress") return "attempted";
  return "not_started";
}

function compare(a: ProblemSummary, b: ProblemSummary, key: SortKey): number {
  switch (key) {
    case "title":
      return a.title.localeCompare(b.title);
    case "category":
      return CATEGORY_ORDER.indexOf(a.category) - CATEGORY_ORDER.indexOf(b.category);
    case "difficulty":
      return DIFFICULTY_RANK[a.difficulty] - DIFFICULTY_RANK[b.difficulty];
    case "est_minutes":
      return a.est_minutes - b.est_minutes;
    case "best":
      return (a.best_result?.value ?? -1) - (b.best_result?.value ?? -1);
  }
}

export function TaskTable({ initial }: { initial: ProblemSummary[] }) {
  const session = useSession();
  const router = useRouter();
  const [problems, setProblems] = useState(initial);
  const [category, setCategory] = useState("all");
  const [difficulty, setDifficulty] = useState("all");
  const [status, setStatus] = useState<Status>("all");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<{ key: SortKey; ascending: boolean } | null>(null);

  // Add the signed-in user's progress and best results to the public list.
  useEffect(() => {
    if (session.status !== "signed_in") return;
    let active = true;
    request<ProblemSummary[]>("/problems")
      .then((rows) => active && setProblems(rows))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [session.status]);

  const categories = useMemo(
    () => CATEGORY_ORDER.filter((key) => problems.some((p) => p.category === key)),
    [problems],
  );

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const rows = problems.filter(
      (p) =>
        (category === "all" || p.category === category) &&
        (difficulty === "all" || p.difficulty === difficulty) &&
        (status === "all" || statusOf(p) === status) &&
        (!needle || `${p.title} ${p.summary}`.toLowerCase().includes(needle)),
    );
    if (!sort) return rows;
    const sorted = [...rows].sort((a, b) => compare(a, b, sort.key));
    return sort.ascending ? sorted : sorted.reverse();
  }, [problems, category, difficulty, status, query, sort]);

  function toggleSort(key: SortKey) {
    setSort((current) =>
      current?.key === key ? { key, ascending: !current.ascending } : { key, ascending: true },
    );
  }

  function openRandom() {
    const pool = visible.length ? visible : problems;
    const pick = pool[Math.floor(Math.random() * pool.length)];
    if (pick) router.push(`/tasks/${pick.id}`);
  }

  const signedIn = session.status === "signed_in";
  const selectClass = "rounded-md border border-field bg-panel px-2.5 py-1.5 text-sm text-ink";

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <label className="sr-only" htmlFor="filter-category">
          Category
        </label>
        <select id="filter-category" className={selectClass} value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="all">All categories</option>
          {categories.map((key) => (
            <option key={key} value={key}>
              {CATEGORY_LABELS[key]}
            </option>
          ))}
        </select>
        <label className="sr-only" htmlFor="filter-difficulty">
          Difficulty
        </label>
        <select id="filter-difficulty" className={selectClass} value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
          <option value="all">All difficulties</option>
          {Object.entries(DIFFICULTY_LABELS).map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
        {signedIn && (
          <>
            <label className="sr-only" htmlFor="filter-status">
              Status
            </label>
            <select id="filter-status" className={selectClass} value={status} onChange={(e) => setStatus(e.target.value as Status)}>
              <option value="all">Any status</option>
              <option value="solved">{PROGRESS_LABELS.solved}</option>
              <option value="attempted">{PROGRESS_LABELS.attempted}</option>
              <option value="not_started">{PROGRESS_LABELS.not_started}</option>
            </select>
          </>
        )}
        <label className="sr-only" htmlFor="filter-search">
          Search tasks
        </label>
        <input
          id="filter-search"
          type="search"
          placeholder="Search tasks"
          className="field min-w-0 flex-1 py-1.5 text-sm sm:max-w-xs"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="button" className="btn-secondary ml-auto py-1.5" onClick={openRandom}>
          Random task
        </button>
      </div>

      <div className="overflow-hidden rounded-md bg-panel">
        <table className="w-full border-collapse text-left text-sm">
          <thead className="text-muted">
            <tr className="border-b border-line">
              <th scope="col" className="w-10 px-3 py-2 font-medium">
                <span className="sr-only">Status</span>
              </th>
              <SortHeader label="Title" column="title" sort={sort} onSort={toggleSort} />
              <SortHeader label="Category" column="category" sort={sort} onSort={toggleSort} className="hidden sm:table-cell" />
              <SortHeader label="Difficulty" column="difficulty" sort={sort} onSort={toggleSort} />
              <SortHeader label="Time" column="est_minutes" sort={sort} onSort={toggleSort} className="hidden md:table-cell" />
              <SortHeader label="Best result" column="best" sort={sort} onSort={toggleSort} className="hidden md:table-cell" align="right" />
            </tr>
          </thead>
          <tbody>
            {visible.map((problem) => (
              <tr key={problem.id} className="border-b border-line last:border-b-0 hover:bg-raised">
                <td className="px-3 py-2.5">
                  <StatusIcon progress={problem.progress} />
                </td>
                <td className="py-2.5 pr-3">
                  <span className="inline-flex items-center gap-2">
                    <Link href={`/tasks/${problem.id}`} className="font-medium text-ink no-underline hover:underline">
                      {problem.title}
                    </Link>
                    {problem.access === "paid" && <LockIcon />}
                  </span>
                </td>
                <td className="hidden py-2.5 pr-3 text-muted sm:table-cell">
                  {CATEGORY_LABELS[problem.category] ?? problem.category}
                </td>
                <td className="py-2.5 pr-3">
                  <Difficulty level={problem.difficulty} />
                </td>
                <td className="hidden py-2.5 pr-3 text-muted md:table-cell">{problem.est_minutes} min</td>
                <td className="hidden py-2.5 pr-4 text-right font-mono text-xs md:table-cell">
                  {problem.best_result?.label ?? <span className="text-muted">—</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {visible.length === 0 && (
          <p className="p-6 text-sm text-muted">
            No tasks match these filters. Clear the search or pick a different filter.
          </p>
        )}
      </div>
    </div>
  );
}

function SortHeader({
  label,
  column,
  sort,
  onSort,
  className = "",
  align = "left",
}: {
  label: string;
  column: SortKey;
  sort: { key: SortKey; ascending: boolean } | null;
  onSort: (key: SortKey) => void;
  className?: string;
  align?: "left" | "right";
}) {
  const active = sort?.key === column;
  return (
    <th
      scope="col"
      aria-sort={active ? (sort.ascending ? "ascending" : "descending") : "none"}
      className={`py-2 pr-3 font-medium ${align === "right" ? "pr-4 text-right" : ""} ${className}`}
    >
      <button
        type="button"
        onClick={() => onSort(column)}
        className={`inline-flex items-center gap-1 rounded-sm hover:text-ink ${active ? "text-ink" : ""}`}
      >
        {label}
        <span aria-hidden="true" className="w-3 text-xs">
          {active ? (sort.ascending ? "▲" : "▼") : ""}
        </span>
      </button>
    </th>
  );
}
