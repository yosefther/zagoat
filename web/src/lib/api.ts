import { config } from "@/config";

/** An API failure, carrying the API's error shape: {"error": {"code", "message", ...}}. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fields: Record<string, string>;
  readonly details: Record<string, unknown>;

  constructor(
    status: number,
    code: string,
    message: string,
    details: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.fields = (details.fields as Record<string, string> | undefined) ?? {};
  }
}

const NETWORK_MESSAGE = "We couldn't reach zagoat. Check your connection and try again.";
const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
};

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.split("; ").find((part) => part.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.slice(name.length + 1)) : null;
}

async function freshCsrfToken(): Promise<string> {
  const data = await request<{ csrf_token: string }>("/csrf");
  return data.csrf_token;
}

async function parseError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as {
      error?: { code?: string; message?: string } & Record<string, unknown>;
    };
    if (body.error?.code && body.error.message) {
      const { code, message, ...details } = body.error;
      return new ApiError(response.status, code, message, details);
    }
  } catch {
    // Fall through to the generic error below.
  }
  return new ApiError(
    response.status,
    "unexpected",
    "Something went wrong on our side. Try again in a minute.",
  );
}

async function send(path: string, options: RequestOptions, csrfToken?: string) {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (csrfToken) headers[config.csrfHeaderName] = csrfToken;
  try {
    return await fetch(`${config.apiUrl}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      credentials: "include",
      signal: options.signal,
      cache: "no-store",
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(0, "network", NETWORK_MESSAGE);
  }
}

/**
 * Call the API from the browser with the session cookie. State-changing requests carry the
 * CSRF token; if the API rejects it (for example after signing in or out), fetch a fresh
 * one and retry once.
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? "GET";
  let response: Response;
  if (UNSAFE_METHODS.has(method)) {
    const token = readCookie(config.csrfCookieName) ?? (await freshCsrfToken());
    response = await send(path, options, token);
    if (response.status === 403) {
      const error = await parseError(response.clone());
      if (error.code === "csrf_failed") {
        response = await send(path, options, await freshCsrfToken());
      }
    }
  } else {
    response = await send(path, options);
  }
  if (!response.ok) throw await parseError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

/** Fetch public data from a Server Component. No cookies are sent. */
export async function serverRequest<T>(path: string): Promise<T | null> {
  const response = await fetch(`${config.apiUrl}${path}`, {
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (response.status === 404) return null;
  if (!response.ok) throw await parseError(response);
  return (await response.json()) as T;
}
