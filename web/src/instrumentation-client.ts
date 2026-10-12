// Runs in the browser before the app starts. Both tools stay off until their keys are set.
import * as Sentry from "@sentry/nextjs";
import posthog from "posthog-js";

import { config } from "@/config";
import { SENTRY_OPTIONS } from "@/lib/sentry";

if (config.sentryDsn) {
  Sentry.init(SENTRY_OPTIONS);
}

if (config.posthogKey) {
  posthog.init(config.posthogKey, {
    api_host: config.posthogHost,
    // No cookies or localStorage: analytics stay anonymous and need no consent banner.
    persistence: "memory",
    capture_pageview: "history_change",
    autocapture: false,
    disable_session_recording: true,
  });
}

export const onRouterTransitionStart = Sentry.captureRouterTransitionStart;
