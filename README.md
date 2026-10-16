# zagoat

Practice the real tasks AI interviews give you.

The build brief in [CLAUDE.md](CLAUDE.md) is the source of truth for scope, rules and milestones.

## Status

Done: Milestones 1 (foundations), 2 (landing page and waitlist), 3 (accounts), 4
(problems), 5 (editor and drafts), 6 (runner) and 7 (business rules).

The web app has the landing page with a waitlist form, privacy and terms placeholders
(marked as drafts to review before launch), a static pricing page and a 404 page. The
design decisions are in [docs/design.md](docs/design.md). Sign-in works with GitHub, Google
or (locally only) a dev user, and the account page covers profile, the code opt-in and
self-service deletion. Problems sync from `problems/` into Postgres and show up at
`/problems`, with two original development tasks (one RAG, one evals). Signed-in users with
access get a Monaco editor with a tab per file and debounced autosave of their draft.
"Run tests" and "Submit solution" queue a job that the runner executes in a fresh,
locked-down container; the page polls for the verdict, tests and metrics. Plans, limits,
progress, hints, walkthroughs, reference solutions, the timer and submission history follow
sections 8 to 11 of the brief (summary below).

## Repo layout

| Path | What it holds |
| --- | --- |
| `api/` | FastAPI app (Python 3.12, SQLAlchemy, Alembic, Pydantic) |
| `web/` | Next.js app (App Router, TypeScript, Tailwind) |
| `runner/` | Worker, Docker sandbox, task image, grading harness, mock LLM and task validation ([runner/README.md](runner/README.md)) |
| `problems/` | One folder per practice task ([problems/README.md](problems/README.md) explains how to write one) |
| `infra/` | docker-compose for local development; server scripts later |

## Prerequisites

- Docker with Compose v2
- [uv](https://docs.astral.sh/uv/). It installs Python 3.12 for you.
- Node.js 22 and npm

## Run it locally

All commands start from the repo root.

1. Build the task image, then start Postgres, Redis and the mock LLM:

   ```sh
   docker build -f runner/images/py312-ml/Dockerfile -t zagoat-py312-ml:dev runner
   docker compose -f infra/docker-compose.yml up -d --build --wait
   ```

   Everything binds to `127.0.0.1` only. If ports 5432 or 6379 are taken, set `POSTGRES_PORT` or
   `REDIS_PORT` before running the command, and update the URLs in `api/.env` to match.
   The first start also creates a `zagoat_test` database for the test suite.

2. Start the API on <http://localhost:8000>:

   ```sh
   cd api
   cp .env.example .env
   uv sync
   uv run alembic upgrade head
   uv run python -m app.problems sync   # load problems/ into the database
   uv run uvicorn app.main:app --reload
   ```

   Check it with `curl localhost:8000/healthz`. Interactive docs are at `/docs` everywhere except
   production.

3. Start the runner worker (it needs Docker):

   ```sh
   cd runner
   cp .env.example .env
   uv sync
   uv run python -m zagoat_runner.worker
   ```

   Without gVisor installed it prints a large warning and uses Docker's default runtime.
   That's fine locally; production refuses to start without gVisor.

4. Start the web app on <http://localhost:3000>:

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
uv run python -m app.problems validate ../problems
```

Tests use the `zagoat_test` database and Redis db 15. To use other instances, set
`TEST_DATABASE_URL` or `TEST_REDIS_URL`.

Runner (grading harness, mock LLM, task validation):

```sh
cd runner
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
uv run python -m zagoat_runner.validate ../problems
ZAGOAT_SANDBOX_TESTS=1 uv run pytest tests/test_sandbox.py   # needs the image and mock LLM
```

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

## Business rules

All rules live in the API; the web app only hides or shows buttons. Every tunable value is
in `api/app/config.py`.

| Rule | Where |
| --- | --- |
| Paid access from the subscriptions table on every request: unrefunded Lifetime, or Pro that is active, past due within 7 days, or canceled before period end | `api/app/plans.py` |
| Free: 10 Submits a day, 30 Runs an hour. Paid: 100 and 120 | `api/app/usage.py` |
| A Submit counts when queued and is refunded on `system_error`; Runs never use Submits; days reset at 00:00 UTC | `api/app/usage.py` |
| One open job per user | `api/app/routes/jobs.py` |
| Progress moves not_started → in_progress (draft save or Run) → attempted (first Submit) → solved (a passing Submit), never backwards | `api/app/progress.py` |
| Hints one at a time, recorded, no penalty; walkthroughs for paid users any time; reference after the first Submit that isn't `system_error` | `api/app/routes/problems.py` |
| After a downgrade, drafts, history and solved states stay; paid problems become read only | `api/app/routes/problems.py` |
| The timer only records time to Submit (stored on the submission and progress) | `api/app/routes/jobs.py` |

`GET /submissions` (all problems) and `PATCH /me` (code opt-in) are small additions to
the route list in the brief.

## How a Run or Submit works

1. The browser posts the files to `POST /problems/{id}/runs` or `/submissions`. The API
   checks access, allows one open job per user, saves a `submissions` row as `queued` and
   pushes a JSON message onto the Redis list `zagoat:jobs`.
2. The worker (`runner/zagoat_runner/worker.py`, 3 slots by default) moves the message to
   a per-slot processing list, drops it as `system_error` if it waited over 5 minutes, and
   starts a fresh container: gVisor, non-root, no capabilities, no-new-privileges,
   read-only root, 200 MB `/tmp`, 1 CPU, 2 GB memory, 64 processes, and the internal
   `zagoat-sandbox` network shared only with the mock LLM. Run mounts the sample tests;
   Submit mounts the hidden tests. Data and tests are read-only; no secrets go in.
3. The worker grades the outcome and posts it to `POST /internal/jobs/{id}/result`
   (shared secret plus IP allowlist). The browser polls `GET /jobs/{id}` every 1.5 s.
4. If the runner never answers, the API closes the job as `system_error` after the queue
   timeout, so a user is never stuck.

The queue is a plain Redis list of JSON messages rather than RQ: RQ pickles job
arguments, which would let anyone who can write to Redis run code on the runner.

## Editor

- Monaco loads from jsDelivr at a pinned version (`monacoBaseUrl` in `web/src/config.ts`)
  instead of being bundled; bundling Monaco's web workers into Next.js is fiddly and the
  CDN keeps the app bundle small. A Content Security Policy must allow that origin.
- Drafts save 1 s after typing stops (`autosaveDelayMs`), never overlap, and retry every
  5 s after a failure. The API only accepts the problem's starter file names and caps a
  draft at 1 MB (`MAX_CODE_BYTES`).

## Dependencies

- Python dependencies are locked in `api/uv.lock`. CI installs with `uv sync --locked`.
- npm dependencies use exact versions (`web/.npmrc` sets `save-exact`) and are locked in
  `web/package-lock.json`.
- GitHub Actions are pinned by commit SHA.
- Dependabot checks uv, npm, Actions and Compose images weekly.

Current major versions: Next.js 16.4, React 19.3, Tailwind 4.3, FastAPI 0.158, SQLAlchemy 2.1,
Postgres 17, Redis 7.
