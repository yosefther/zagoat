import type { Metadata } from "next";

import { DraftNotice } from "@/components/DraftNotice";

export const metadata: Metadata = { title: "Terms of service" };

export default function TermsPage() {
  return (
    <main className="container-page py-16">
      <article className="prose-page">
        <h1 className="text-3xl font-bold">Terms of service</h1>
        <DraftNotice />
        <p>By using zagoat you agree to these terms.</p>

        <h2>Your account</h2>
        <p>
          Sign in with GitHub or Google. Keep your account to yourself, and don&apos;t share
          paid content outside it.
        </p>

        <h2>Fair use</h2>
        <ul>
          <li>Don&apos;t try to break, overload or escape the code sandbox.</li>
          <li>Don&apos;t scrape tasks, hidden tests or reference solutions.</li>
          <li>Daily limits on runs and submissions keep the service fair for everyone.</li>
        </ul>

        <h2>Your code</h2>
        <p>
          You own the code you write. You give us permission to store and run it so we can
          grade it and show you your history.
        </p>

        <h2>Payments</h2>
        <p>
          Paid plans are billed by our payment provider. You can cancel a subscription at any
          time and keep access until the end of the period you paid for.
        </p>

        <h2>No warranty</h2>
        <p>
          zagoat is a practice tool. We work hard to keep it running, but we can&apos;t promise
          it will always be available or that practice guarantees any interview result.
        </p>
      </article>
    </main>
  );
}
