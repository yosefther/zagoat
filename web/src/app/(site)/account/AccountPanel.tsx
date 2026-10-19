"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";

import { ApiError, request } from "@/lib/api";
import { PLAN_LABELS, formatLocalDateTime, formatLocalTime } from "@/lib/format";
import { useSession } from "@/lib/session";
import type { Me } from "@/lib/types";

const DELETE_PHRASE = "delete my account";

export function AccountPanel() {
  const session = useSession();
  const router = useRouter();
  const id = useId();
  const [saving, setSaving] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const params = useSearchParams();
  const justPaid = params.get("checkout") === "success";
  const { refresh } = session;

  // A provider's webhook can land a moment after the redirect: check a few times.
  useEffect(() => {
    if (!justPaid) return;
    const timers = [1500, 4000, 8000].map((ms) => setTimeout(() => void refresh(), ms));
    return () => timers.forEach(clearTimeout);
  }, [justPaid, refresh]);

  // Visitors go to sign-in. After signing out or deleting the account here, the action that
  // ended the session decides where to go instead.
  const wasSignedIn = useRef(false);
  useEffect(() => {
    if (session.status === "signed_in") wasSignedIn.current = true;
    if (session.status === "signed_out" && !wasSignedIn.current) {
      router.replace("/signin?return_to=%2Faccount");
    }
  }, [session.status, router]);

  if (session.status !== "signed_in") {
    return <p className="text-muted">Loading your account…</p>;
  }
  const { user } = session;

  async function toggleOptIn(next: boolean) {
    setSaving(true);
    setError(null);
    session.setUser({ ...user, code_opt_in: next });
    try {
      session.setUser(await request<Me>("/me", { method: "PATCH", body: { code_opt_in: next } }));
    } catch (err) {
      session.setUser(user);
      setError(err instanceof ApiError ? err.message : "Couldn't save your choice. Try again.");
    } finally {
      setSaving(false);
    }
  }

  async function openPortal() {
    setError(null);
    try {
      const { url } = await request<{ url: string }>("/billing/portal");
      window.location.assign(url);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't open billing. Try again.");
    }
  }

  async function deleteAccount() {
    setDeleting(true);
    setError(null);
    try {
      await request("/me", { method: "DELETE" });
      session.setUser(null);
      router.push("/?deleted=1");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't delete. Try again.");
      setDeleting(false);
    }
  }

  return (
    <div className="flex max-w-2xl flex-col gap-8">
      {justPaid && (
        <p role="status" className="rounded-md border border-success p-3 text-sm text-success">
          Thanks for your purchase. Your plan updates as soon as the payment is confirmed.
        </p>
      )}
      {error && (
        <p role="alert" className="rounded-md border border-danger p-3 text-sm text-danger">
          {error}
        </p>
      )}

      <div className="overflow-hidden rounded-md bg-panel">
        <section className="flex items-center gap-4 p-6" aria-label="Profile">
          {user.avatar_url ? (
            <Image
              src={user.avatar_url}
              alt=""
              width={56}
              height={56}
              unoptimized
              className="size-14 rounded-full border border-line"
            />
          ) : null}
          <div>
            <p className="font-heading text-lg font-bold">{user.name ?? "No name set"}</p>
            <p className="text-muted">{user.email}</p>
          </div>
        </section>

        <section className="flex flex-col gap-2 border-t border-line p-6">
          <h2 className="text-lg font-bold">Plan</h2>
          <p>
            {PLAN_LABELS[user.plan.name]}
            {user.plan.access_ends_at && (
              <span className="text-muted">
                {" "}
                · access until {formatLocalDateTime(user.plan.access_ends_at)}
              </span>
            )}
          </p>
          <p className="text-sm text-muted">
            {user.usage.submits_used} of {user.usage.submits_limit} Submits used today (resets at{" "}
            {formatLocalTime(user.usage.submits_reset_at)}) · {user.usage.runs_used} of{" "}
            {user.usage.runs_limit} test runs this hour
          </p>
          {user.plan.tier === "free" ? (
            <Link href="/pricing" className="self-start text-sm">
              See plans
            </Link>
          ) : (
            <button type="button" className="btn-secondary self-start" onClick={openPortal}>
              Manage billing
            </button>
          )}
        </section>

        <section className="flex flex-col gap-3 border-t border-line p-6">
          <h2 className="text-lg font-bold">Your code</h2>
          <p className="text-sm text-muted">
            We use your code only to grade it. You can let us use it to improve tasks, for
            example to find common mistakes. You can change this at any time.
          </p>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              className="size-4 accent-brand"
              checked={user.code_opt_in}
              disabled={saving}
              onChange={(event) => toggleOptIn(event.target.checked)}
            />
            Let zagoat use my code to improve tasks
          </label>
        </section>

      </div>

      <section className="flex flex-col gap-3 border-l-2 border-danger pl-6">
        <h2 className="text-lg font-bold">Delete account</h2>
        <p className="text-sm text-muted">
          This removes your profile, drafts, submissions and progress right away and can&apos;t
          be undone. Backups expire within 30 days. If you pay for a plan, cancel it first in
          the billing portal.
        </p>
        <label htmlFor={`${id}-confirm`} className="text-sm font-medium">
          Type &ldquo;{DELETE_PHRASE}&rdquo; to confirm
        </label>
        <input
          id={`${id}-confirm`}
          className="field max-w-sm"
          value={confirmText}
          onChange={(event) => setConfirmText(event.target.value)}
          autoComplete="off"
        />
        <div>
          <button
            type="button"
            className="btn border border-danger bg-panel text-danger"
            disabled={confirmText.trim().toLowerCase() !== DELETE_PHRASE || deleting}
            onClick={deleteAccount}
          >
            {deleting ? "Deleting…" : "Delete my account permanently"}
          </button>
        </div>
      </section>
    </div>
  );
}
