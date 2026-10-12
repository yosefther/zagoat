import type { Metadata } from "next";

export const metadata: Metadata = { title: "Pricing" };

// Static until billing lands (Milestone 8), when prices come from the API's config.
export default function PricingPage() {
  return (
    <main className="container-page flex flex-col gap-8 py-16">
      <h1 className="text-3xl font-bold">Pricing</h1>
      <p className="max-w-prose text-muted">
        zagoat is in development. Join the waitlist on the home page to hear when it opens.
      </p>
      <div className="grid gap-6 md:grid-cols-2">
        <section className="card flex flex-col gap-2 p-6">
          <h2 className="text-xl font-bold">Free</h2>
          <p className="text-muted">A few free tasks with the editor, tests and hints.</p>
        </section>
        <section className="card flex flex-col gap-2 p-6">
          <h2 className="text-xl font-bold">Lifetime</h2>
          <p className="text-muted">
            One payment for every task, hint and walkthrough. Limited to the first 100 buyers.
            Price announced at launch.
          </p>
        </section>
      </div>
    </main>
  );
}
