"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, request } from "@/lib/api";
import { useSession } from "@/lib/session";
import type { ProblemDetail } from "@/lib/types";

/** The signed-in side of the problem page: lock states, then the editor and results. */
export function ProblemWorkspace({ problemId }: { problemId: string }) {
  const session = useSession();
  const pathname = usePathname();
  const [problem, setProblem] = useState<ProblemDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (session.status === "loading") return;
    let active = true;
    request<ProblemDetail>(`/problems/${encodeURIComponent(problemId)}`)
      .then((data) => active && setProblem(data))
      .catch((err) => active && setError(err instanceof ApiError ? err.message : String(err)));
    return () => {
      active = false;
    };
  }, [problemId, session.status]);

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
  return (
    <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-auto p-6">
      {Object.entries(problem.starter_files ?? {}).map(([name, code]) => (
        <figure key={name} className="card overflow-hidden">
          <figcaption className="border-b border-border px-3 py-1.5 font-mono text-xs text-muted">
            {name}
          </figcaption>
          <pre className="overflow-x-auto p-3 font-mono text-xs">
            <code>{code}</code>
          </pre>
        </figure>
      ))}
    </div>
  );
}

function Notice({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="m-6 flex max-w-lg flex-col gap-3 rounded-xl border border-border bg-surface p-6">
      <h2 className="text-lg font-bold">{title}</h2>
      <div className="flex flex-col gap-3 text-muted">{children}</div>
    </div>
  );
}
