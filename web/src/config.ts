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
  /** PostHog project key. Analytics stay off when it is unset. */
  posthogKey: string | null;
  posthogHost: string;
  /** Sentry DSN for browser and server errors. Sentry stays off when it is unset. */
  sentryDsn: string | null;
  environment: string;
  /** Name of the readable cookie the API uses for CSRF tokens. */
  csrfCookieName: string;
  csrfHeaderName: string;
};

type RawConfig = {
  apiUrl: string | undefined;
  posthogKey?: string | undefined;
  posthogHost?: string | undefined;
  sentryDsn?: string | undefined;
  environment?: string | undefined;
};

const DEFAULT_API_URL = "http://localhost:8000";
const DEFAULT_POSTHOG_HOST = "https://eu.i.posthog.com";

function optional(value: string | undefined): string | null {
  const trimmed = value?.trim();
  return trimmed ? trimmed : null;
}

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
  return {
    apiUrl: apiUrl.replace(/\/+$/, ""),
    posthogKey: optional(raw.posthogKey),
    posthogHost: optional(raw.posthogHost) ?? DEFAULT_POSTHOG_HOST,
    sentryDsn: optional(raw.sentryDsn),
    environment: optional(raw.environment) ?? "development",
    csrfCookieName: "zagoat_csrf",
    csrfHeaderName: "X-CSRF-Token",
  };
}

export const config: WebConfig = parseConfig({
  apiUrl: process.env.NEXT_PUBLIC_API_URL,
  posthogKey: process.env.NEXT_PUBLIC_POSTHOG_KEY,
  posthogHost: process.env.NEXT_PUBLIC_POSTHOG_HOST,
  sentryDsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_ENVIRONMENT,
});
