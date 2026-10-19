import type { Metadata } from "next";
import { Suspense } from "react";

import { SignInPanel } from "./SignInPanel";

export const metadata: Metadata = { title: "Sign in" };

export default function SignInPage() {
  return (
    <main className="container-page flex flex-1 flex-col items-start gap-6 py-16">
      <h1 className="text-3xl font-bold">Sign in to zagoat</h1>
      <p className="max-w-prose text-muted">
        Use your GitHub or Google account. We only read your name, email and avatar.
      </p>
      <Suspense fallback={<p className="text-muted">Loading sign-in options…</p>}>
        <SignInPanel />
      </Suspense>
    </main>
  );
}
