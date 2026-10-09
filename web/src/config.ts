/**
 * Web app configuration.
 *
 * Every tunable value for the web app lives here. `NEXT_PUBLIC_*` variables are
 * inlined at build time, so each one must be read with a literal
 * `process.env.NEXT_PUBLIC_…` reference (no dynamic lookups).
 */

export type WebConfig = {
  /** Base URL of the zagoat JSON API, without a trailing slash. */
  apiUrl: string;
};

type RawConfig = {
  apiUrl: string | undefined;
};

const DEFAULT_API_URL = "http://localhost:8000";

export function parseConfig(raw: RawConfig): WebConfig {
  const apiUrl = raw.apiUrl?.trim() || DEFAULT_API_URL;
  let parsed: URL;
  try {
    parsed = new URL(apiUrl);
  } catch {
    throw new Error(
      `NEXT_PUBLIC_API_URL must be an absolute URL such as ${DEFAULT_API_URL}; got "${apiUrl}".`,
    );
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error(`NEXT_PUBLIC_API_URL must use http or https; got "${apiUrl}".`);
  }
  return { apiUrl: apiUrl.replace(/\/+$/, "") };
}

export const config: WebConfig = parseConfig({
  apiUrl: process.env.NEXT_PUBLIC_API_URL,
});
