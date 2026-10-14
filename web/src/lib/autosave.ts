export type Files = Record<string, string>;
export type SaveStatus = "saved" | "unsaved" | "saving" | "error";

/**
 * Debounced, sequential draft saving. Each change restarts the timer; saves never overlap,
 * and a failed save is retried until a newer change replaces it.
 */
export class Autosaver {
  private timer: ReturnType<typeof setTimeout> | null = null;
  private pending: Files | null = null;
  private inFlight: Promise<void> | null = null;
  private disposed = false;

  constructor(
    private readonly save: (files: Files) => Promise<void>,
    private readonly onStatus: (status: SaveStatus) => void,
    private readonly delayMs: number,
    private readonly retryMs: number,
  ) {}

  update(files: Files): void {
    this.pending = files;
    this.onStatus("unsaved");
    this.schedule(this.delayMs);
  }

  /** Save now if anything is waiting. Resolves once everything known so far is saved. */
  async flush(): Promise<void> {
    this.clearTimer();
    while (this.inFlight) await this.inFlight;
    const snapshot = this.pending;
    if (!snapshot || this.disposed) return;
    this.pending = null;
    this.onStatus("saving");
    this.inFlight = this.save(snapshot).then(
      () => {
        this.inFlight = null;
        if (!this.pending) this.onStatus("saved");
      },
      () => {
        this.inFlight = null;
        this.pending ??= snapshot;
        this.onStatus("error");
        this.schedule(this.retryMs);
      },
    );
    await this.inFlight;
  }

  hasUnsavedChanges(): boolean {
    return this.pending !== null || this.inFlight !== null;
  }

  dispose(): void {
    this.disposed = true;
    this.clearTimer();
  }

  private schedule(ms: number): void {
    this.clearTimer();
    this.timer = setTimeout(() => void this.flush(), ms);
  }

  private clearTimer(): void {
    if (this.timer) clearTimeout(this.timer);
    this.timer = null;
  }
}
