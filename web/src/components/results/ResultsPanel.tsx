import type { Job, MetricResult, TestResult } from "@/lib/types";
import { VERDICT_LABELS, formatMetric, verdictTone } from "@/lib/verdicts";

const TONE_CLASSES = {
  success: "border-success text-success",
  danger: "border-danger text-danger",
  muted: "border-field text-muted",
};

const OUTCOME_ICONS: Record<TestResult["outcome"], string> = {
  passed: "✓",
  failed: "✗",
  error: "!",
  skipped: "–",
};

type Props = {
  job: Job | null;
  error: string | null;
};

export function ResultsPanel({ job, error }: Props) {
  return (
    <section
      aria-label="Results"
      aria-live="polite"
      className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-4 text-sm"
    >
      {error && (
        <p role="alert" className="text-danger">
          {error}
        </p>
      )}
      {!job && !error && (
        <p className="text-muted">
          Run the sample tests as often as you like. Submit runs the hidden tests and metrics.
        </p>
      )}
      {job && job.status !== "done" && (
        <p className="text-muted">
          {job.status === "queued" ? "Waiting for a sandbox…" : "Running your code…"}
        </p>
      )}
      {job?.status === "done" && job.verdict && <Verdict job={job} />}
    </section>
  );
}

function Verdict({ job }: { job: Job }) {
  const verdict = job.verdict!;
  const label = job.kind === "run" ? "Sample tests" : "Submission";
  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <span
          className={`rounded-full border px-2.5 py-0.5 font-display font-bold ${TONE_CLASSES[verdictTone(verdict)]}`}
        >
          {VERDICT_LABELS[verdict]}
        </span>
        <span className="text-muted">
          {label}
          {job.tests_total ? ` · ${job.tests_passed} of ${job.tests_total} tests passed` : ""}
          {job.duration_ms ? ` · ${(job.duration_ms / 1000).toFixed(1)} s` : ""}
        </span>
      </div>
      {job.message && <p>{job.message}</p>}
      {job.metrics.length > 0 && <Metrics metrics={job.metrics} />}
      {job.tests.length > 0 && (
        <ul className="flex flex-col gap-1.5">
          {job.tests.map((test, index) => (
            <li key={index} className="flex gap-2">
              <span
                role="img"
                aria-label={test.outcome}
                className={test.outcome === "passed" ? "text-success" : "text-danger"}
              >
                {OUTCOME_ICONS[test.outcome]}
              </span>
              <div className="min-w-0">
                <p>{test.name}</p>
                {test.message && (
                  <pre className="mt-1 font-mono text-xs whitespace-pre-wrap text-muted">
                    {test.message}
                  </pre>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
      {(job.stdout || job.stderr) && (
        <details open={verdict !== "passed"}>
          <summary className="cursor-pointer text-muted">Output</summary>
          <pre className="mt-2 max-h-64 overflow-auto rounded-lg border border-border bg-code p-3 font-mono text-xs whitespace-pre-wrap">
            {job.stdout}
            {job.stderr}
          </pre>
        </details>
      )}
    </>
  );
}

function Metrics({ metrics }: { metrics: MetricResult[] }) {
  return (
    <table className="w-full max-w-md border-collapse text-left">
      <thead>
        <tr className="text-muted">
          <th className="py-1 font-medium">Metric</th>
          <th className="py-1 font-medium">Value</th>
          <th className="py-1 font-medium">Target</th>
        </tr>
      </thead>
      <tbody>
        {metrics.map((metric) => (
          <tr key={metric.name} className="border-t border-border">
            <td className="py-1 font-mono text-xs">{metric.name}</td>
            <td
              className={`py-1 ${metric.met === true ? "text-success" : metric.met === false ? "text-danger" : ""}`}
            >
              {formatMetric(metric.value)}
            </td>
            <td className="py-1 text-muted">
              {metric.threshold === null
                ? "–"
                : `${metric.goal === "at_most" ? "≤" : "≥"} ${metric.threshold}`}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
