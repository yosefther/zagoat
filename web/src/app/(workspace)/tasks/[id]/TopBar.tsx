"use client";

import Link from "next/link";
import { Suspense } from "react";

import { useProblem } from "./ProblemContext";
import { ShortcutsHelp } from "./ShortcutsHelp";
import { useWorkspace } from "./WorkspaceContext";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { UserMenu } from "@/components/UserMenu";
import { formatDuration, formatLocalTime } from "@/lib/format";

export type Neighbors = {
  previous: string | null;
  next: string | null;
  back: { href: string; label: string };
};

type Props = {
  title: string;
  neighbors: Neighbors;
};

/** Workspace top bar: navigation, title, timer, remaining Submits, Run and Submit. */
export function TopBar({ title, neighbors }: Props) {
  const { problem } = useProblem();
  const { canSolve, busy, start, timer, submitsLeft } = useWorkspace();
  const usage = problem?.usage;

  return (
    <header className="flex h-[var(--header-height)] shrink-0 items-center gap-3 border-b border-line bg-page px-3">
      <Logo withName={false} size={26} />
      <nav aria-label="Task navigation" className="flex items-center">
        <Link href={neighbors.back.href} className="btn-quiet max-w-48 truncate px-2.5">
          {neighbors.back.label}
        </Link>
        <NavArrow href={neighbors.previous} label="Previous task" glyph="‹" />
        <NavArrow href={neighbors.next} label="Next task" glyph="›" />
      </nav>
      <p className="min-w-0 flex-1 truncate font-heading font-bold" title={title}>
        {title}
      </p>

      {canSolve && (
        <div className="flex items-center gap-4 text-sm">
          <label className="inline-flex items-center gap-2 text-muted" title="Records time to Submit">
            <input
              type="checkbox"
              className="size-4 accent-brand"
              checked={timer.running}
              onChange={(event) => (event.target.checked ? timer.start() : timer.stop())}
            />
            Timer
            {timer.elapsedSeconds !== null && (
              <span className="font-mono text-ink">{formatDuration(timer.elapsedSeconds)}</span>
            )}
          </label>
          {usage && submitsLeft !== null && (
            <span className="text-muted">
              {submitsLeft} of {usage.submits_limit} Submits left, resets at{" "}
              {formatLocalTime(usage.submits_reset_at)}
              {submitsLeft === 0 && problem?.plan === "free" && (
                <>
                  . <Link href="/pricing">Upgrade for more</Link>
                </>
              )}
            </span>
          )}
          <button
            type="button"
            className="btn-secondary"
            disabled={busy !== null}
            onClick={() => start("run")}
            title="Ctrl/Cmd + Enter"
          >
            {busy === "run" ? "Running…" : "Run tests"}
          </button>
          <button
            type="button"
            className="btn-primary"
            disabled={busy !== null || submitsLeft === 0}
            onClick={() => start("submit")}
            title="Ctrl/Cmd + Shift + Enter"
          >
            {busy === "submit" ? "Submitting…" : "Submit solution"}
          </button>
        </div>
      )}

      <div className="flex items-center gap-1">
        <ShortcutsHelp />
        <ThemeToggle />
        <Suspense fallback={<span className="inline-block h-9 w-9" aria-hidden="true" />}>
          <UserMenu />
        </Suspense>
      </div>
    </header>
  );
}

function NavArrow({ href, label, glyph }: { href: string | null; label: string; glyph: string }) {
  if (!href) {
    return (
      <span className="btn-quiet px-2.5 opacity-40" aria-hidden="true">
        {glyph}
      </span>
    );
  }
  return (
    <Link href={href} className="btn-quiet px-2.5 text-lg leading-none" aria-label={label} title={label}>
      {glyph}
    </Link>
  );
}
