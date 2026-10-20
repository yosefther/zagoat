import { describe, expect, it } from "vitest";

import { safeReturnPath, signInUrl } from "./auth";

describe("safeReturnPath", () => {
  it.each([
    ["/tasks", "/tasks"],
    [null, "/"],
    ["https://evil.example", "/"],
    ["//evil.example", "/"],
    ["/\\evil.example", "/"],
  ])("maps %s to %s", (input, expected) => {
    expect(safeReturnPath(input)).toBe(expected);
  });
});

describe("signInUrl", () => {
  it("points at the API's start route with the return path", () => {
    expect(signInUrl("github", "/account")).toBe(
      "http://localhost:8000/auth/github/start?return_to=%2Faccount",
    );
  });
});
