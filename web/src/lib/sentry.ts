import type { BrowserOptions } from "@sentry/nextjs";

import { config } from "@/config";

/** Shared Sentry options. Collects no user info, cookies, headers or bodies (user code). */
export const SENTRY_OPTIONS: BrowserOptions = {
  dsn: config.sentryDsn ?? undefined,
  environment: config.environment,
  tracesSampleRate: 0,
  dataCollection: {
    userInfo: false,
    cookies: false,
    httpHeaders: false,
    httpBodies: [],
    urlQueryParams: false,
  },
};
