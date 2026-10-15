import { config } from "@/config";
import { request } from "@/lib/api";
import type { Job } from "@/lib/types";

/** Poll a job until it's done, reporting every state. Rejects if it takes far too long. */
export async function pollJob(
  jobId: string,
  onUpdate: (job: Job) => void,
  signal: AbortSignal,
): Promise<Job> {
  const started = Date.now();
  for (;;) {
    const job = await request<Job>(`/jobs/${jobId}`, { signal });
    onUpdate(job);
    if (job.status === "done") return job;
    if (Date.now() - started > config.jobPollGiveUpMs) {
      throw new Error("This is taking much longer than usual. Reload the page to check again.");
    }
    await new Promise<void>((resolve, reject) => {
      const timer = setTimeout(resolve, config.jobPollIntervalMs);
      signal.addEventListener("abort", () => {
        clearTimeout(timer);
        reject(new DOMException("Aborted", "AbortError"));
      });
    });
  }
}
