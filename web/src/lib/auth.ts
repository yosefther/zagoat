import { config } from "@/config";

export const PROVIDER_LABELS: Record<string, string> = {
  github: "Continue with GitHub",
  google: "Continue with Google",
  dev: "Continue as dev user (local only)",
};

/** Messages for /signin?error=<code>, set by the API's OAuth callback. */
export const SIGNIN_ERRORS: Record<string, string> = {
  access_denied: "Sign-in was cancelled. Choose a provider to try again.",
  expired:
    "That sign-in attempt expired or was opened in a different browser. Start again below.",
  email_unverified:
    "Your account has no verified email address. Verify one with the provider, then try again.",
  provider_error: "The sign-in provider didn't respond as expected. Try again in a minute.",
  provider_unavailable: "That sign-in option isn't available. Choose another one.",
  rate_limited: "Too many sign-in attempts from your network. Try again in an hour.",
};

export function signInUrl(provider: string, returnTo: string): string {
  const params = new URLSearchParams({ return_to: returnTo });
  return `${config.apiUrl}/auth/${provider}/start?${params}`;
}

/** Keep sign-in redirects on this site, matching the API's own check. */
export function safeReturnPath(value: string | null | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) {
    return "/";
  }
  return value;
}
