import Link from "next/link";

import { SampleTaskCard } from "@/components/SampleTaskCard";
import { WaitlistForm } from "@/components/WaitlistForm";
import { SAMPLE_TASKS } from "@/content/samples";

const STEPS = [
  {
    title: "Read the brief",
    body: "Each task describes a broken or missing piece of a real AI system, with data and starter code.",
  },
  {
    title: "Fix the code in your browser",
    body: "Write Python in the editor and run the sample tests as often as you like.",
  },
  {
    title: "Get graded",
    body: "Submit to run hidden tests and metric checks, then compare with the reference solution.",
  },
];

export default function Home() {
  return (
    <main>
      <section className="container-page flex flex-col gap-6 py-16 sm:py-24">
        <h1 className="max-w-3xl text-3xl font-bold tracking-tight sm:text-4xl">
          Practice the real tasks AI interviews give you.
        </h1>
        <p className="max-w-prose text-lg text-muted">
          Fix a RAG pipeline, debug a training loop, write an eval. Realistic 30–60 minute
          tasks in Python, graded by hidden tests and metrics, not puzzles.
        </p>
        <WaitlistForm />
      </section>

      <section aria-labelledby="samples-heading" className="border-y border-border bg-surface">
        <div className="container-page flex flex-col gap-8 py-16">
          <h2 id="samples-heading" className="text-2xl font-bold">
            What you&apos;ll practice
          </h2>
          <div className="grid gap-6 md:grid-cols-3">
            {SAMPLE_TASKS.map((task) => (
              <SampleTaskCard key={task.title} task={task} />
            ))}
          </div>
        </div>
      </section>

      <section aria-labelledby="how-heading" className="container-page flex flex-col gap-8 py-16">
        <h2 id="how-heading" className="text-2xl font-bold">
          How it works
        </h2>
        <ol className="grid gap-6 md:grid-cols-3">
          {STEPS.map((step, index) => (
            <li key={step.title} className="flex gap-4">
              <span
                aria-hidden="true"
                className="grid size-8 shrink-0 place-items-center rounded-full border border-accent-edge bg-accent font-display font-bold text-on-accent"
              >
                {index + 1}
              </span>
              <div>
                <h3 className="font-bold">{step.title}</h3>
                <p className="text-muted">{step.body}</p>
              </div>
            </li>
          ))}
        </ol>
        <p>
          <Link href="/pricing">See pricing</Link>
        </p>
      </section>
    </main>
  );
}
