import { describe, expect, it } from "vitest";

import { parseConfig } from "./config";

describe("parseConfig", () => {
  it("defaults to the local API", () => {
    expect(parseConfig({ apiUrl: undefined }).apiUrl).toBe("http://localhost:8000");
    expect(parseConfig({ apiUrl: "  " }).apiUrl).toBe("http://localhost:8000");
  });

  it("strips trailing slashes", () => {
    expect(parseConfig({ apiUrl: "https://api.zagoat.io//" }).apiUrl).toBe(
      "https://api.zagoat.io",
    );
  });

  it("rejects values that are not absolute http(s) URLs", () => {
    expect(() => parseConfig({ apiUrl: "api.zagoat.io" })).toThrow(/absolute URL/);
    expect(() => parseConfig({ apiUrl: "ftp://api.zagoat.io" })).toThrow(/http or https/);
  });

  it("leaves monitoring off unless keys are set", () => {
    const off = parseConfig({ apiUrl: undefined, posthogKey: " ", sentryDsn: undefined });
    expect(off.posthogKey).toBeNull();
    expect(off.sentryDsn).toBeNull();

    const on = parseConfig({ apiUrl: undefined, posthogKey: "phc_123", sentryDsn: "https://k@s.io/1" });
    expect(on.posthogKey).toBe("phc_123");
    expect(on.sentryDsn).toBe("https://k@s.io/1");
  });
});
