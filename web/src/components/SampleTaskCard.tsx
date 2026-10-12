import type { SampleTask } from "@/content/samples";

export function SampleTaskCard({ task }: { task: SampleTask }) {
  return (
    <article className="card flex min-w-0 flex-col gap-3 p-5">
      <p className="text-xs font-medium tracking-wide text-muted uppercase">
        {task.category} · {task.difficulty} · {task.minutes} min
      </p>
      <h3 className="text-lg font-bold">{task.title}</h3>
      <p className="text-sm text-muted">{task.brief}</p>
      <figure className="mt-auto overflow-hidden rounded-lg border border-border bg-code">
        <figcaption className="border-b border-border px-3 py-1.5 font-mono text-xs text-muted">
          {task.file}
        </figcaption>
        <pre className="overflow-x-auto p-3 font-mono text-xs leading-relaxed">
          <code>{task.code}</code>
        </pre>
      </figure>
    </article>
  );
}
