import { describe, expect, it } from "vitest";

import { parseConfig } from "./config";

describe("parseConfig", () => {
  it("defaults to the local API", () => {
    expect(parseConfig({ apiUrl: undefined })).toEqual({ apiUrl: "http://localhost:8000" });
    expect(parseConfig({ apiUrl: "  " })).toEqual({ apiUrl: "http://localhost:8000" });
  });

  it("strips trailing slashes", () => {
    expect(parseConfig({ apiUrl: "https://api.zagoat.io//" })).toEqual({
      apiUrl: "https://api.zagoat.io",
    });
  });

  it("rejects values that are not absolute http(s) URLs", () => {
    expect(() => parseConfig({ apiUrl: "api.zagoat.io" })).toThrow(/absolute URL/);
    expect(() => parseConfig({ apiUrl: "ftp://api.zagoat.io" })).toThrow(/http or https/);
  });
});
