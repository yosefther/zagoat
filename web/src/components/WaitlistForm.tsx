"use client";

import Link from "next/link";
import { useId, useState, type FormEvent } from "react";

import { ApiError, request } from "@/lib/api";

type Status =
  | { kind: "idle" }
  | { kind: "submitting" }
  | { kind: "joined" }
  | { kind: "error"; message: string; fields: Record<string, string> };

export function WaitlistForm({ source = "landing" }: { source?: string }) {
  const id = useId();
  const [email, setEmail] = useState("");
  const [consent, setConsent] = useState(false);
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!consent) {
      setStatus({
        kind: "error",
        message: "Tick the box to agree to launch emails.",
        fields: { consent: "Tick the box to agree to launch emails." },
      });
      return;
    }
    setStatus({ kind: "submitting" });
    try {
      await request("/waitlist", { method: "POST", body: { email, consent, source } });
      setStatus({ kind: "joined" });
    } catch (error) {
      if (error instanceof ApiError) {
        setStatus({ kind: "error", message: error.message, fields: error.fields });
      } else {
        setStatus({
          kind: "error",
          message: "Something went wrong. Try again in a minute.",
          fields: {},
        });
      }
    }
  }

  if (status.kind === "joined") {
    return (
      <p role="status" className="card max-w-xl p-4 font-medium text-success">
        You&apos;re on the list. We&apos;ll email {email} when zagoat launches.
      </p>
    );
  }

  const fields = status.kind === "error" ? status.fields : {};
  const emailError = fields.email ? "Enter a valid email address, like you@example.com." : null;
  const consentError = fields.consent ?? null;

  return (
    <form onSubmit={onSubmit} noValidate className="flex max-w-xl flex-col gap-3">
      <label htmlFor={`${id}-email`} className="text-sm font-medium">
        Email address
      </label>
      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          id={`${id}-email`}
          type="email"
          name="email"
          autoComplete="email"
          required
          placeholder="you@example.com"
          className="field sm:flex-1"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          aria-invalid={emailError ? true : undefined}
          aria-describedby={emailError ? `${id}-email-error` : undefined}
        />
        <button type="submit" className="btn-primary" disabled={status.kind === "submitting"}>
          {status.kind === "submitting" ? "Joining…" : "Join the waitlist"}
        </button>
      </div>
      {emailError && (
        <p id={`${id}-email-error`} className="text-sm text-danger">
          {emailError}
        </p>
      )}
      <div className="flex items-start gap-2 text-sm">
        <input
          id={`${id}-consent`}
          type="checkbox"
          className="mt-1 size-4 accent-[var(--ink)]"
          checked={consent}
          onChange={(event) => setConsent(event.target.checked)}
          aria-invalid={consentError ? true : undefined}
          aria-describedby={consentError ? `${id}-consent-error` : undefined}
        />
        <label htmlFor={`${id}-consent`} className="text-muted">
          Email me when zagoat launches. I&apos;ve read the{" "}
          <Link href="/privacy">privacy policy</Link>.
        </label>
      </div>
      {consentError && (
        <p id={`${id}-consent-error`} className="text-sm text-danger">
          {consentError}
        </p>
      )}
      <p aria-live="polite" className="text-sm text-danger">
        {status.kind === "error" && !emailError && !consentError ? status.message : ""}
      </p>
    </form>
  );
}
