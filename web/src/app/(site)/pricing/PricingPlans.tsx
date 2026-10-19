"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, request } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { useSession } from "@/lib/session";
import type { PlanName, Plans } from "@/lib/types";

export function PricingPlans() {
  const session = useSession();
  const params = useSearchParams();
  const [plans, setPlans] = useState<Plans | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<PlanName | null>(null);

  useEffect(() => {
    if (session.status === "loading") return;
    let active = true;
    request<Plans>("/billing/plans")
      .then((data) => active && setPlans(data))
      .catch((err) => active && setError(err instanceof ApiError ? err.message : String(err)));
    return () => {
      active = false;
    };
  }, [session.status]);

  async function buy(plan: PlanName) {
    setBusy(plan);
    setError(null);
    try {
      const { url } = await request<{ url: string }>("/billing/checkout", {
        method: "POST",
        body: { plan },
      });
      window.location.assign(url);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Checkout didn't start. Try again.");
      setBusy(null);
    }
  }

  if (!plans) {
    return error ? (
      <p role="alert" className="text-danger">
        {error}
      </p>
    ) : (
      <p className="text-muted">Loading plans…</p>
    );
  }

  const signedIn = session.status === "signed_in";
  const current = plans.current_plan;
  const signInLink = `/signin?${new URLSearchParams({ return_to: "/pricing" })}`;

  function action(plan: PlanName, label: string) {
    if (!plans?.payments_enabled) {
      return <p className="text-sm text-muted">Payments open at launch.</p>;
    }
    if (!signedIn) {
      return (
        <Link href={signInLink} className="btn-primary">
          Sign in to buy
        </Link>
      );
    }
    return (
      <button type="button" className="btn-primary" disabled={busy !== null} onClick={() => buy(plan)}>
        {busy === plan ? "Opening checkout…" : label}
      </button>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {params.get("checkout") === "canceled" && (
        <p role="status" className="text-muted">
          Checkout canceled. You haven&apos;t been charged.
        </p>
      )}
      {error && (
        <p role="alert" className="text-danger">
          {error}
        </p>
      )}
      <div className="grid overflow-hidden rounded-md bg-panel md:auto-cols-fr md:grid-flow-col">
        <PlanCard title="Free" price={formatPrice(0, plans.currency)} current={current === "free"}>
          <p>A few free problems with the editor, tests, hints and reference solutions.</p>
          {!signedIn && (
            <Link href={signInLink} className="btn-secondary">
              Sign in to start
            </Link>
          )}
        </PlanCard>

        <PlanCard
          title="Lifetime"
          price={
            plans.lifetime_price_cents === null
              ? "Price at launch"
              : `${formatPrice(plans.lifetime_price_cents, plans.currency)} once`
          }
          current={current === "lifetime"}
        >
          <p>One payment for every problem, hint and walkthrough, for as long as zagoat runs.</p>
          {plans.lifetime_price_cents !== null && (
            <p className="text-sm text-muted">
              {plans.lifetime_available
                ? `Only for the first 100 buyers: ${plans.lifetime_remaining} left.`
                : "Sold out."}
            </p>
          )}
          {current !== "lifetime" && plans.lifetime_available && action("lifetime", "Buy Lifetime")}
          {plans.lifetime_price_cents === null && (
            <p className="text-sm text-muted">Lifetime opens at launch.</p>
          )}
        </PlanCard>

        {plans.pro_enabled && (
          <PlanCard
            title="Pro"
            price={`${formatPrice(plans.pro_monthly_price_cents, plans.currency)} a month`}
            current={current === "pro_monthly" || current === "pro_yearly"}
          >
            <p>Everything in Lifetime, billed monthly or yearly. Cancel any time.</p>
            <p className="text-sm text-muted">
              Or {formatPrice(plans.pro_yearly_price_cents, plans.currency)} a year.
            </p>
            {current === "free" || current === null ? (
              <div className="flex flex-wrap gap-2">
                {action("pro_monthly", "Subscribe monthly")}
                {plans.payments_enabled && signedIn && (
                  <button
                    type="button"
                    className="btn-secondary"
                    disabled={busy !== null}
                    onClick={() => buy("pro_yearly")}
                  >
                    {busy === "pro_yearly" ? "Opening checkout…" : "Subscribe yearly"}
                  </button>
                )}
              </div>
            ) : null}
          </PlanCard>
        )}
      </div>
    </div>
  );
}

function PlanCard({
  title,
  price,
  current,
  children,
}: {
  title: string;
  price: string;
  current: boolean;
  children: React.ReactNode;
}) {
  return (
    <section className="flex flex-col gap-3 border-line p-6 not-first:border-t md:not-first:border-t-0 md:not-first:border-l">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-lg font-bold">{title}</h3>
        {current && (
          <span className="text-xs font-medium text-success">Your plan</span>
        )}
      </div>
      <p className="font-heading text-2xl font-bold">{price}</p>
      <div className="flex flex-col gap-3 text-muted [&>a]:self-start [&>button]:self-start">
        {children}
      </div>
    </section>
  );
}
