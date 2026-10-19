import type { Metadata } from "next";

import { DraftNotice } from "@/components/DraftNotice";

export const metadata: Metadata = { title: "Privacy policy" };

export default function PrivacyPage() {
  return (
    <main className="container-page py-16">
      <article className="prose-page">
        <h1 className="text-3xl font-bold">Privacy policy</h1>
        <DraftNotice />
        <p>
          This page explains what zagoat collects, why, and how to have it removed. We collect
          as little as we can.
        </p>

        <h2>What we collect</h2>
        <ul>
          <li>
            <strong>Waitlist:</strong> your email address, where you signed up, and your consent
            to launch emails.
          </li>
          <li>
            <strong>Account:</strong> your email, name and avatar from GitHub or Google when you
            sign in. We never see your password.
          </li>
          <li>
            <strong>Your work:</strong> the code you write, your drafts, submissions, results,
            hints you reveal, and your progress.
          </li>
          <li>
            <strong>Payments:</strong> handled by our payment provider. We store your plan and
            its status, never your card details.
          </li>
        </ul>

        <h2>How we use it</h2>
        <ul>
          <li>We use your code only to grade it, unless you opt in to something else.</li>
          <li>We email waitlist members about the launch, and nothing else without consent.</li>
          <li>
            We use privacy-friendly product analytics that don&apos;t set tracking cookies, and
            an error tracker that receives technical details when something breaks.
          </li>
        </ul>

        <h2>Cookies</h2>
        <p>
          We set a session cookie when you sign in and a security cookie that protects forms.
          We don&apos;t use advertising or tracking cookies.
        </p>

        <h2>Deleting your data</h2>
        <p>
          You can delete your account from the account page at any time. That removes your
          profile, drafts, submissions and progress at once. Copies in our encrypted backups
          expire within 30 days. Billing records stay with the payment provider, as the law
          requires. To leave the waitlist, email us.
        </p>

        <h2>Contact</h2>
        <p>Email privacy@zagoat.io (placeholder address, to confirm before launch).</p>
      </article>
    </main>
  );
}
