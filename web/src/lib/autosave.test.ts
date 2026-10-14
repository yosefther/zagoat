import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Autosaver, type Files, type SaveStatus } from "./autosave";

function setup(save: (files: Files) => Promise<void> = async () => {}) {
  const statuses: SaveStatus[] = [];
  const saveSpy = vi.fn(save);
  const saver = new Autosaver(saveSpy, (s) => statuses.push(s), 1000, 5000);
  return { saver, saveSpy, statuses };
}

describe("Autosaver", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("saves once after typing stops", async () => {
    const { saver, saveSpy, statuses } = setup();
    saver.update({ "a.py": "1" });
    await vi.advanceTimersByTimeAsync(500);
    saver.update({ "a.py": "12" });
    await vi.advanceTimersByTimeAsync(999);
    expect(saveSpy).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(1);

    expect(saveSpy).toHaveBeenCalledExactlyOnceWith({ "a.py": "12" });
    expect(statuses.at(-1)).toBe("saved");
  });

  it("never overlaps saves and sends the newest files last", async () => {
    let release: () => void = () => {};
    const { saver, saveSpy, statuses } = setup(
      () => new Promise<void>((resolve) => (release = resolve)),
    );
    saver.update({ "a.py": "v1" });
    await vi.advanceTimersByTimeAsync(1000);
    saver.update({ "a.py": "v2" });
    await vi.advanceTimersByTimeAsync(1000);
    expect(saveSpy).toHaveBeenCalledTimes(1);

    release();
    await vi.advanceTimersByTimeAsync(0);
    release();
    await vi.advanceTimersByTimeAsync(0);

    expect(saveSpy.mock.calls.map((call) => call[0]["a.py"])).toEqual(["v1", "v2"]);
    expect(statuses.at(-1)).toBe("saved");
  });

  it("retries a failed save", async () => {
    let fail = true;
    const { saver, saveSpy, statuses } = setup(async () => {
      if (fail) throw new Error("offline");
    });
    saver.update({ "a.py": "1" });
    await vi.advanceTimersByTimeAsync(1000);
    expect(statuses.at(-1)).toBe("error");
    expect(saver.hasUnsavedChanges()).toBe(true);

    fail = false;
    await vi.advanceTimersByTimeAsync(5000);

    expect(saveSpy).toHaveBeenCalledTimes(2);
    expect(statuses.at(-1)).toBe("saved");
    expect(saver.hasUnsavedChanges()).toBe(false);
  });

  it("flush saves immediately", async () => {
    const { saver, saveSpy } = setup();
    saver.update({ "a.py": "1" });

    await saver.flush();

    expect(saveSpy).toHaveBeenCalledOnce();
  });
});
