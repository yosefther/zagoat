"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useProblem } from "@/app/problems/[id]/ProblemContext";
import { SolveArea } from "@/app/problems/[id]/SolveArea";
import { SolveWorkspace } from "@/app/problems/[id]/SolveWorkspace";

/** The right-hand side of the problem page: lock states, then the editor and results. */
export function ProblemWorkspace() {
  const { problem, error } = useProblem();
  const pathname = usePathname();

  if (error) {
    return <Notice title="We couldn't load your workspace">{error}</Notice>;
  }
  if (!problem) {
    return <p className="p-6 text-muted">Loading your workspace…</p>;
  }
  if (problem.lock === "sign_in") {
    const params = new URLSearchParams({ return_to: pathname });
    return (
      <Notice title="Sign in to solve this problem">
        <p>Sign in with GitHub or Google to open the editor, run tests and submit.</p>
        <Link href={`/signin?${params}`} className="btn-primary self-start">
          Sign in to start
        </Link>
      </Notice>
    );
  }
  if (problem.read_only) {
    return (
      <div className="flex min-h-0 flex-1 flex-col">
        <p className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-border bg-code px-4 py-2 text-sm">
          Your plan no longer includes this problem, so your code is read only.
          <Link href="/pricing">See plans</Link>
        </p>
        <SolveArea problem={problem} readOnly />
      </div>
    );
  }
  if (problem.lock === "paid") {
    return (
      <Notice title="This problem is part of Lifetime and Pro">
        <p>You can read the statement for free. Upgrade to open the editor and submit.</p>
        <Link href="/pricing" className="btn-primary self-start">
          See plans
        </Link>
      </Notice>
    );
  }
  return <SolveWorkspace problem={problem} />;
}

function Notice({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="m-6 flex max-w-lg flex-col gap-3 rounded-xl border border-border bg-surface p-6">
      <h2 className="text-lg font-bold">{title}</h2>
      <div className="flex flex-col gap-3 text-muted">{children}</div>
    </div>
  );
}
