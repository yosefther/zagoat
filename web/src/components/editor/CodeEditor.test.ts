import { describe, expect, it } from "vitest";

import { toHex6 } from "./CodeEditor";

describe("toHex6", () => {
  it.each([
    ["#fff", "#ffffff"],
    [" #96D927 ", "#96d927"],
    ["#0f120b", "#0f120b"],
  ])("normalizes %s", (input, expected) => {
    expect(toHex6(input)).toBe(expected);
  });
});
