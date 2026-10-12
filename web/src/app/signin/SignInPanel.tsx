"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { request } from "@/lib/api";
import { PROVIDER_LABELS, SIGNIN_ERRORS, safeReturnPath, signInUrl } from "@/lib/auth";

export function SignInPanel() {
  const params = useSearchParams();
  const returnTo = safeReturnPath(params.get("return_to"));
  const errorCode = params.get("error");
  const [providers, setProviders] = useState<string[] | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);

  useEffect(() => {
    request<{ providers: string[] }>("/auth/providers")
      .then((data) => setProviders(data.providers))
      .catch(() => setLoadFailed(true));
  }, []);

  return (
    <div className="flex w-full max-w-sm flex-col gap-3">
      {errorCode && (
        <p role="alert" className="rounded-lg border border-danger p-3 text-sm text-danger">
          {SIGNIN_ERRORS[errorCode] ?? "Sign-in didn't work. Try again."}
        </p>
      )}
      {loadFailed && (
        <p role="alert" className="text-sm text-danger">
          We couldn&apos;t load sign-in options. Check your connection and reload the page.
        </p>
      )}
      {providers?.length === 0 && (
        <p className="text-sm text-muted">
          No sign-in providers are configured. Set GitHub or Google OAuth credentials in the
          API&apos;s environment.
        </p>
      )}
      {providers?.map((provider) => (
        <a
          key={provider}
          href={signInUrl(provider, returnTo)}
          className={provider === "dev" ? "btn-secondary" : "btn-primary"}
        >
          {PROVIDER_LABELS[provider] ?? `Continue with ${provider}`}
        </a>
      ))}
      <p className="text-sm text-muted">
        By signing in you agree to the <Link href="/terms">terms</Link> and{" "}
        <Link href="/privacy">privacy policy</Link>.
      </p>
    </div>
  );
}
