import type { Metadata } from "next";
import { Suspense } from "react";

import { PricingPlans } from "./PricingPlans";

export const metadata: Metadata = {
  title: "Pricing",
  description: "Practice free, or unlock every task, hint and walkthrough.",
};

const CAPABILITIES: [string, string, string][] = [
  ["Browse problems and read statements", "Yes", "Yes"],
  ["Editor, Run and Submit on free problems", "Yes", "Yes"],
  ["Editor, Run and Submit on paid problems", "No", "Yes"],
  ["Hints", "On free problems", "Yes"],
  ["Walkthroughs", "No", "Yes"],
  ["Reference solution", "After your first Submit", "After your first Submit"],
  ["Submits per day", "10", "100 (fair use)"],
  ["Test runs per hour", "30", "120"],
];

export default function PricingPage() {
  return (
    <main className="container-page flex flex-col gap-10 py-16">
      <div className="flex flex-col gap-3">
        <h1 className="text-3xl font-bold">Pricing</h1>
        <p className="max-w-prose text-muted">
          Start free. Upgrade when you want every task, every hint and the full walkthroughs.
        </p>
      </div>
      <Suspense fallback={<p className="text-muted">Loading plans…</p>}>
        <PricingPlans />
      </Suspense>
      <section aria-labelledby="compare-heading" className="flex flex-col gap-4">
        <h2 id="compare-heading" className="text-xl font-bold">
          What each plan includes
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[32rem] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-line">
                <th className="py-2 pr-4 font-medium text-muted">Capability</th>
                <th className="py-2 pr-4 font-medium">Free</th>
                <th className="py-2 font-medium">Lifetime and Pro</th>
              </tr>
            </thead>
            <tbody>
              {CAPABILITIES.map(([name, free, paid]) => (
                <tr key={name} className="border-b border-line">
                  <td className="py-2 pr-4">{name}</td>
                  <td className="py-2 pr-4 text-muted">{free}</td>
                  <td className="py-2">{paid}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-sm text-muted">
          Lifetime and Pro unlock exactly the same things; they differ only in how you pay.
        </p>
      </section>
    </main>
  );
}
