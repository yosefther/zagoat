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
      {/* The one bold element: the climb. Text stays on open sky, left of the range. */}
      <section className="relative overflow-hidden">
        <div className="mx-auto grid max-w-[90rem] grid-cols-[minmax(0,1fr)] items-end md:min-h-[min(44rem,calc(100dvh-var(--header-height)))] md:grid-cols-[minmax(0,38rem)_minmax(0,1fr)]">
          <div className="flex flex-col gap-6 px-4 pt-12 pb-6 sm:px-6 md:self-center md:py-16 md:pl-[max(1.5rem,calc((100vw-72rem)/2))]">
            <h1 className="font-heading text-hero leading-[0.92] font-bold tracking-[-0.01em]">
              Practice the real tasks AI interviews give you.
            </h1>
            <p className="max-w-[38ch] text-lg text-muted">
              Fix a RAG pipeline, debug a training loop, write an eval. Each task takes 30 to 60
              minutes in Python and is graded by hidden tests and metrics.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link href="/tasks" className="btn-primary px-5 py-2.5 text-base">
                Browse tasks
              </Link>
              <a href="#waitlist" className="btn-secondary px-5 py-2.5 text-base">
                Get launch news
              </a>
            </div>
          </div>
          <div className="h-[18rem] sm:h-[24rem] md:h-full md:min-h-[34rem]">
            <HeroVisual />
          </div>
        </div>
      </section>

      <section aria-labelledby="samples-heading" className="bg-panel">
        <div className="container-page flex flex-col gap-10 py-16">
          <div className="flex max-w-[60ch] flex-col gap-3">
            <h2 id="samples-heading" className="text-3xl">
              Two tasks you can open today
            </h2>
            <p className="text-muted">
              Each one is a small, broken piece of a real AI system, with data, starter code and
              tests. Read any statement for free, and sign in to solve.
            </p>
          </div>
          <ol className="flex flex-col">
            {SAMPLE_TASKS.map((task) => (
              <li
                key={task.id}
                className="grid grid-cols-[minmax(0,1fr)] gap-6 border-t border-line py-10 first:border-t-0 first:pt-0 last:pb-0 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)] lg:gap-12"
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
                  <h3 className="text-2xl">{task.title}</h3>
                  <p className="max-w-[52ch] text-muted">{task.brief}</p>
                  <Link href={`/tasks/${task.id}`} className="self-start font-medium">
                    Read the task
                  </Link>
                </div>
                <figure className="min-w-0 self-start rounded-sm bg-raised">
                  <figcaption className="px-4 pt-3 text-sm text-muted">{task.file}</figcaption>
                  <pre className="overflow-x-auto px-4 pt-2 pb-4 font-mono text-[0.8125rem] leading-relaxed">
                    <code>{task.code}</code>
                  </pre>
                </figure>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section aria-labelledby="pricing-heading">
        <div className="container-page flex flex-col gap-8 py-16">
          <h2 id="pricing-heading" className="text-3xl">
            Pricing
          </h2>
          <Suspense fallback={<p className="text-muted">Loading plans…</p>}>
            <PricingPlans />
          </Suspense>
          <Link href="/pricing" className="self-start text-sm">
            Compare what each plan includes
          </Link>
        </div>
      </section>

      <section id="waitlist" aria-labelledby="waitlist-heading" className="bg-panel">
        <div className="container-page grid grid-cols-[minmax(0,1fr)] gap-8 py-16 md:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
          <div className="flex flex-col gap-3">
            <h2 id="waitlist-heading" className="text-3xl">
              Get launch news
            </h2>
            <p className="max-w-[44ch] text-muted">
              One email when zagoat opens, and one when new tasks land. Nothing else.
            </p>
          </div>
          <WaitlistForm />
        </div>
      </section>
    </main>
  );
}
