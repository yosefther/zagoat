# zagoat

Practice the real tasks AI interviews give you.

The build brief in [CLAUDE.md](CLAUDE.md) is the source of truth for scope, rules and milestones.

## Status

Done: Milestones 1 (foundations), 2 (landing page and waitlist) and 3 (accounts).

The web app has the landing page with a waitlist form, privacy and terms placeholders
(marked as drafts to review before launch), a static pricing page and a 404 page. The
design decisions are in [docs/design.md](docs/design.md). Sign-in works with GitHub, Google
or (locally only) a dev user, and the account page covers profile, the code opt-in and
self-service deletion.

## Repo layout

| Path | What it holds |
| --- | --- |
| `api/` | FastAPI app (Python 3.12, SQLAlchemy, Alembic, Pydantic) |
| `web/` | Next.js app (App Router, TypeScript, Tailwind) |
| `runner/` | Worker, sandbox images and mock LLM (Milestone 6) |
| `problems/` | One folder per practice task (Milestone 4) |
| `infra/` | docker-compose for local development; server scripts later |

## Prerequisites

- Docker with Compose v2
- [uv](https://docs.astral.sh/uv/). It installs Python 3.12 for you.
- Node.js 22 and npm

## Run it locally

All commands start from the repo root.

1. Start Postgres and Redis:

   ```sh
   docker compose -f infra/docker-compose.yml up -d --wait
   ```

   Both bind to `127.0.0.1` only. If ports 5432 or 6379 are taken, set `POSTGRES_PORT` or
   `REDIS_PORT` before running the command, and update the URLs in `api/.env` to match.
   The first start also creates a `zagoat_test` database for the test suite.

2. Start the API on <http://localhost:8000>:

   ```sh
   cd api
   cp .env.example .env
   uv sync
   uv run alembic upgrade head
   uv run uvicorn app.main:app --reload
   ```

   Check it with `curl localhost:8000/healthz`. Interactive docs are at `/docs` everywhere except
   production.

3. Start the web app on <http://localhost:3000>:

   ```sh
   cd web
   cp .env.example .env.local
   npm install
   npm run dev
   ```

To stop the services, run `docker compose -f infra/docker-compose.yml down`. Add `-v` to also delete
the data volumes.

## Tests and lint

CI runs exactly these commands on every push to `main` and on every pull request (see
`.github/workflows/ci.yml`).

API (needs Postgres and Redis running):

```sh
cd api
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

Tests use the `zagoat_test` database and Redis db 15. To use other instances, set
`TEST_DATABASE_URL` or `TEST_REDIS_URL`.

Web:

```sh
cd web
npm run lint
npm run typecheck
npm test
npm run build
```

## Configuration

Each service keeps every tunable value in one config module:

- API: `api/app/config.py`, read from environment variables or `api/.env`. With
  `ENVIRONMENT=production`, the API refuses to start unless `DATABASE_URL`, `REDIS_URL`,
  `WEB_ORIGIN`, `API_ORIGIN` and `SECRET_KEY` are set explicitly, `COOKIE_SECURE=true`, and
  `DEV_LOGIN_ENABLED` is off.
- Web: `web/src/config.ts`. `NEXT_PUBLIC_*` values are baked into the browser bundle at build
  time, so they must never hold secrets.

The `.env.example` files list every variable. Real `.env` files are gitignored.

## Sign-in

- GitHub and Google use the OAuth authorization-code flow with PKCE, a one-time state
  stored in Redis and a state cookie that ties the flow to the browser. A provider appears
  on the sign-in page only when its client id and secret are set in `api/.env`.
  - GitHub: create an OAuth app with callback `<API_ORIGIN>/auth/github/callback`.
  - Google: create an OAuth client (web application) with redirect URI
    `<API_ORIGIN>/auth/google/callback`.
- A verified email links a second provider to the same user.
- For local development without OAuth apps, `DEV_LOGIN_ENABLED=true` (the default in
  `api/.env.example`) adds "Continue as dev user", which signs in as `dev@example.com`.
- Sessions are random tokens in an HTTP-only, SameSite=Lax cookie; only their SHA-256 is
  stored. `DELETE /me` removes the user and, through cascading foreign keys, everything
  tied to them.

## Security basics

- Every state-changing route needs a CSRF token: the web app calls `GET /csrf`, which sets a
  readable `zagoat_csrf` cookie, and echoes it in the `X-CSRF-Token` header. Tokens are
  signed and bound to the session, so planted or stale tokens are rejected; the web client
  fetches a fresh one and retries once.
- CORS allows only `WEB_ORIGIN`, with credentials.
- Errors always use one shape: `{"error": {"code", "message", ...}}`. Validation errors add
  `fields`, rate limits add `retry_after_seconds` and a `Retry-After` header.
- Per-IP rate limits use Redis fixed windows (`api/app/ratelimit.py`). In production, run
  uvicorn with `--proxy-headers` behind the reverse proxy so the client IP is real.

## Monitoring and analytics

Both stay off until keys are set; no accounts are needed for local development.

- Sentry: `SENTRY_DSN` (API) and `NEXT_PUBLIC_SENTRY_DSN` (web). No user info, cookies,
  headers or request bodies are sent, so user code never reaches Sentry.
- PostHog: `NEXT_PUBLIC_POSTHOG_KEY`. Runs with in-memory persistence (no cookies or
  localStorage), page views only, no autocapture or session recording.

## Database migrations

```sh
cd api
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

New migration files are lint-fixed and formatted with ruff automatically.

## Dependencies

- Python dependencies are locked in `api/uv.lock`. CI installs with `uv sync --locked`.
- npm dependencies use exact versions (`web/.npmrc` sets `save-exact`) and are locked in
  `web/package-lock.json`.
- GitHub Actions are pinned by commit SHA.
- Dependabot checks uv, npm, Actions and Compose images weekly.

Current major versions: Next.js 16.4, React 19.3, Tailwind 4.3, FastAPI 0.158, SQLAlchemy 2.1,
Postgres 17, Redis 7.
