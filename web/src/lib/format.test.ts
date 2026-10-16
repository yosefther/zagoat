import { describe, expect, it } from "vitest";

import { formatDuration } from "./format";

describe("formatDuration", () => {
  it.each([
    [0, "00:00"],
    [65, "01:05"],
    [3599, "59:59"],
    [3725, "1:02:05"],
  ])("formats %i seconds as %s", (seconds, expected) => {
    expect(formatDuration(seconds)).toBe(expected);
  });
});
