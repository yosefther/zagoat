"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Group, Panel, Separator, useDefaultLayout } from "react-resizable-panels";
import type { ReactNode } from "react";

import { ConsolePanel } from "./ConsolePanel";
import { EditorPanel } from "./EditorPanel";
import { Description, LeftPanel } from "./LeftPanel";
import { useProblem } from "./ProblemContext";
import { TopBar } from "./TopBar";
import { WorkspaceProvider } from "./WorkspaceContext";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import type { ProblemDetail } from "@/lib/types";
import { useIsDesktop } from "@/lib/useIsDesktop";

type Props = {
  publicProblem: ProblemDetail;
  neighbors: { previous: string | null; next: string | null };
  statement: ReactNode;
};

export function Workspace({ publicProblem, neighbors, statement }: Props) {
  const desktop = useIsDesktop();
  return (
    <WorkspaceProvider problemId={publicProblem.id}>
      {/* Phones and narrow screens: read the statement; solving needs a desktop. */}
      <div className="flex flex-col lg:hidden">
        <header className="flex h-[var(--header-height)] items-center justify-between border-b border-line px-4">
          <Logo size={24} />
          <div className="flex items-center gap-1">
            <Link href="/problems" className="btn-quiet px-2.5">
              Problems
            </Link>
            <ThemeToggle />
          </div>
        </header>
        <main id="main" className="flex flex-col gap-4 px-4 py-6">
          <p className="rounded-md bg-raised p-3 text-sm">
            Solving works on desktop. Open this page on a larger screen to write and run code.
          </p>
          <Description problem={publicProblem} statement={statement} />
        </main>
      </div>

      <div className="hidden h-dvh flex-col lg:flex">
        <TopBar title={publicProblem.title} neighbors={neighbors} />
        <main id="main" className="min-h-0 flex-1 bg-page p-2">
          {desktop && <Panes publicProblem={publicProblem} statement={statement} />}
        </main>
      </div>
    </WorkspaceProvider>
  );
}

function Panes({ publicProblem, statement }: Pick<Props, "publicProblem" | "statement">) {
  const columns = useDefaultLayout({ id: "zagoat-workspace-columns" });
  const rows = useDefaultLayout({ id: "zagoat-workspace-rows" });
  return (
    <Group
      orientation="horizontal"
      defaultLayout={columns.defaultLayout}
      onLayoutChanged={columns.onLayoutChanged}
      className="h-full"
    >
      <Panel id="statement" defaultSize="42" minSize="22" className="overflow-hidden rounded-md">
        <LeftPanel publicProblem={publicProblem} statement={statement} />
      </Panel>
      <ResizeHandle orientation="vertical" />
      <Panel id="code" defaultSize="58" minSize="30">
        <Group
          orientation="vertical"
          defaultLayout={rows.defaultLayout}
          onLayoutChanged={rows.onLayoutChanged}
          className="h-full"
        >
          <Panel id="editor" defaultSize="64" minSize="20" className="overflow-hidden rounded-md">
            <CodeSide />
          </Panel>
          <ResizeHandle orientation="horizontal" />
          <Panel id="console" defaultSize="36" minSize="12" className="overflow-hidden rounded-md">
            <ConsolePanel />
          </Panel>
        </Group>
      </Panel>
    </Group>
  );
}

function ResizeHandle({ orientation }: { orientation: "vertical" | "horizontal" }) {
  const vertical = orientation === "vertical";
  return (
    <Separator
      className={`group flex items-center justify-center ${vertical ? "w-2" : "h-2"} focus-visible:outline-2`}
    >
      <span
        className={`rounded-full bg-line transition-colors group-hover:bg-brand group-data-[separator=active]:bg-brand ${
          vertical ? "h-8 w-0.5" : "h-0.5 w-8"
        }`}
      />
    </Separator>
  );
}

/** The editor, or why it isn't available. */
function CodeSide() {
  const { problem, error } = useProblem();
  const pathname = usePathname();

  if (error) return <Notice title="We couldn't load your workspace">{error}</Notice>;
  if (!problem) return <p className="h-full bg-panel p-6 text-sm text-muted">Loading your workspace…</p>;
  if (problem.lock === "sign_in") {
    const params = new URLSearchParams({ return_to: pathname });
    return (
      <Notice title="Sign in to solve this task">
        <p>Sign in with GitHub or Google to open the editor, run tests and submit.</p>
        <Link href={`/signin?${params}`} className="btn-primary self-start">
          Sign in to start
        </Link>
      </Notice>
    );
  }
  if (problem.read_only) {
    return (
      <div className="flex h-full flex-col">
        <p className="flex flex-wrap items-center gap-x-3 bg-raised px-4 py-2 text-sm">
          Your plan no longer includes this task, so your code is read only.
          <Link href="/pricing">See plans</Link>
        </p>
        <div className="min-h-0 flex-1">
          <EditorPanel problem={problem} readOnly />
        </div>
      </div>
    );
  }
  if (problem.lock === "paid") {
    return (
      <Notice title="This task is part of Lifetime and Pro">
        <p>The statement is free to read. Upgrade to open the editor, run tests and submit.</p>
        <Link href="/pricing" className="btn-primary self-start">
          See plans
        </Link>
      </Notice>
    );
  }
  return <EditorPanel problem={problem} readOnly={false} />;
}

function Notice({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="flex h-full items-start bg-panel p-8">
      <div className="flex max-w-md flex-col gap-3">
        <h2 className="text-lg font-bold">{title}</h2>
        <div className="flex flex-col gap-3 text-muted">{children}</div>
      </div>
    </div>
  );
}
