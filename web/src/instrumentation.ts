// Server-side error reporting. Stays off until NEXT_PUBLIC_SENTRY_DSN is set.
import * as Sentry from "@sentry/nextjs";

import { config } from "@/config";
import { SENTRY_OPTIONS } from "@/lib/sentry";

export function register() {
  if (config.sentryDsn) {
    Sentry.init(SENTRY_OPTIONS);
  }
}

export const onRequestError = Sentry.captureRequestError;
