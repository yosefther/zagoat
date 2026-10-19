import Link from "next/link";
import { Suspense } from "react";

import { PricingPlans } from "./pricing/PricingPlans";
import { HeroVisual } from "@/components/hero/HeroVisual";
import { ProblemMeta } from "@/components/ProblemMeta";
import { WaitlistForm } from "@/components/WaitlistForm";
import { SAMPLE_TASKS } from "@/content/samples";

export default function Home() {
  return (
    <main>
      <section className="container-page grid grid-cols-[minmax(0,1fr)] items-center gap-8 py-12 md:grid-cols-[1fr_1.1fr] md:py-20">
        <div className="flex flex-col gap-6">
          <h1 className="text-3xl font-bold sm:text-4xl">
            Practice the real tasks AI interviews give you.
          </h1>
          <p className="max-w-[46ch] text-lg text-muted">
            Fix a RAG pipeline, debug a training loop, write an eval. 30 to 60 minute tasks in
            Python, graded by hidden tests and metrics instead of puzzles.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link href="/problems" className="btn-primary px-5 py-2.5 text-base">
              Browse problems
            </Link>
            <a href="#waitlist" className="btn-secondary px-5 py-2.5 text-base">
              Get launch news
            </a>
          </div>
        </div>
        <HeroVisual />
      </section>

      <section aria-labelledby="samples-heading" className="border-t border-line bg-panel">
        <div className="container-page flex flex-col gap-8 py-14">
          <div className="flex flex-col gap-2">
            <h2 id="samples-heading" className="text-2xl font-bold">
              Tasks you can open today
            </h2>
            <p className="max-w-[60ch] text-muted">
              Every task is a small, broken piece of a real AI system with data, starter code
              and tests. Read the statement for free; sign in to solve it.
            </p>
          </div>
          <ol className="flex flex-col">
            {SAMPLE_TASKS.map((task) => (
              <li
                key={task.id}
                className="grid grid-cols-[minmax(0,1fr)] gap-5 border-t border-line py-8 first:border-t-0 first:pt-0 lg:grid-cols-[1fr_1.15fr]"
              >
                <div className="flex flex-col gap-3">
                  <ProblemMeta
                    problem={{
                      category: task.category,
                      difficulty: task.difficulty,
                      est_minutes: task.minutes,
                      access: "free",
                    }}
                  />
                  <h3 className="text-xl font-bold">{task.title}</h3>
                  <p className="text-muted">{task.brief}</p>
                  <Link href={`/problems/${task.id}`} className="self-start font-medium">
                    Read the task
                  </Link>
                </div>
                <figure className="min-w-0 overflow-hidden rounded-md bg-raised">
                  <figcaption className="border-b border-line px-4 py-2 font-mono text-xs text-muted">
                    {task.file}
                  </figcaption>
                  <pre className="overflow-x-auto p-4 font-mono text-sm leading-relaxed">
                    <code>{task.code}</code>
                  </pre>
                </figure>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section aria-labelledby="pricing-heading" className="border-t border-line">
        <div className="container-page flex flex-col gap-6 py-14">
          <h2 id="pricing-heading" className="text-2xl font-bold">
            Pricing
          </h2>
          <Suspense fallback={<p className="text-muted">Loading plans…</p>}>
            <PricingPlans />
          </Suspense>
          <Link href="/pricing" className="self-start text-sm">
            Compare plans in detail
          </Link>
        </div>
      </section>

      <section id="waitlist" aria-labelledby="waitlist-heading" className="border-t border-line bg-panel">
        <div className="container-page flex flex-col gap-4 py-14">
          <h2 id="waitlist-heading" className="text-2xl font-bold">
            Get launch news
          </h2>
          <p className="max-w-[60ch] text-muted">
            One email when zagoat opens, and one when new tasks land. Nothing else.
          </p>
          <WaitlistForm />
        </div>
      </section>
    </main>
  );
}
