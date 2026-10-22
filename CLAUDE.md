# zagoat.io — build brief for Claude

This file is the source of truth for building the zagoat.io MVP. Read it fully at the start of every session. If a request in chat conflicts with this file, point out the conflict and ask before acting.

## 1. How we work

- Build one milestone at a time (section 14). Before writing code for a milestone, post a short plan (files, steps, risks) and wait for my OK.
- When a milestone is done: run lint and tests, update the README, summarize what you built, list every assumption you made, and stop. Don't start the next milestone until I say so.
- Keep running costs under about $50 a month. Ask before adding any paid service, new infrastructure or major dependency.
- Put every tunable number (limits, prices, caps, timeouts) in one config module per service, never inline. Values marked "proposed" are defaults I may change.
- Write tests for every business rule in sections 8 to 11. Business rules live in the API; the browser only hides or shows buttons.
- Never commit secrets. Use gitignored `.env` files and a checked-in `.env.example`.
- Prefer boring, well-known libraries, and explain any trade-off you make.
- Practice tasks must be original. Never copy real interview questions, and use only synthetic or clearly licensed data.

## 2. Product

zagoat.io is a practice platform for AI engineer interviews. Instead of LeetCode-style puzzles, users solve realistic 30–60 minute tasks like the ones AI interviews give: fixing a RAG pipeline, debugging training code, writing evals, serving a model.

- Core promise: "Practice the real tasks AI interviews give you."
- Audience: mid-level to senior AI engineers; English; global.
- Language for tasks: Python only.
- Devices: desktop for solving. On mobile, users can browse the problem list and read statements, with a note to solve on desktop.
- Modes: practice by default; an optional timer toggle records time to Submit and never changes the verdict.

MVP features: landing page with waitlist, problem list, problem page (statement, Monaco editor, Run and Submit, results with tests and metrics), submission history, hints, walkthroughs (paid), reference solution after the first Submit, pricing page, account page.

Not in the MVP: AI feedback or AI hints, mock interviews, leaderboards, certificates, email/password login, an admin panel, languages other than Python.

## 3. Stack

| Part | Choice |
| --- | --- |
| Web app | Next.js (App Router), TypeScript, Tailwind, Monaco editor; deployed on Vercel free tier |
| 3D (landing hero only) | three.js through React Three Fiber and drei, lazy-loaded |
| API | FastAPI on Python 3.11+, with SQLAlchemy, Alembic and Pydantic |
| Database | Postgres |
| Queue | Redis plus one worker process (RQ or similar) |
| Runner | Separate server: Docker with the gVisor runtime (runsc), the worker, a mock LLM service |
| Sign-in | GitHub and Google OAuth only; server-side sessions in HTTP-only cookies |
| Payments | Provider not chosen yet (Paddle, Lemon Squeezy or Stripe); code against an interface (section 10) |
| Monitoring | Sentry for errors; PostHog or Plausible for analytics |
| Backups | Nightly pg_dump to object storage off the server |
| Problems | Files in Git (`problems/<id>/problem.yaml`), validated in CI |
| Code hosting | Private GitHub repo; GitHub Actions for CI |

Repo layout:

```
/web        Next.js app
/api        FastAPI app, including the problem sync command
/runner     worker, sandbox images, mock LLM
/problems   one folder per task
/infra      docker-compose for local dev, server setup and deploy scripts
```

## 4. Architecture

- The browser talks to one JSON API. The web app never receives hidden tests or graders.
- App server (VPS 1) runs the API, Postgres and Redis. Only API code touches the database.
- Runner server (VPS 2) runs the worker, the sandbox containers and the mock LLM. It holds no database or payment credentials.
- Redis accepts connections only from the API and the runner's IP.
- Job flow: the API checks the request → saves a submission row as `queued` → enqueues a job in Redis → the worker pulls it and starts a fresh sandbox → the sandbox runs and grades the code → the worker posts the result to `POST /internal/jobs/{id}/result` (shared secret plus IP allowlist) → the API saves it and updates progress → the browser polls `GET /jobs/{id}` every 1–2 s until it's done.
- Local dev: docker-compose runs Postgres, Redis, the API, the worker and the mock LLM on one machine. If gVisor isn't installed locally, fall back to the default runtime with a loud warning. Production must refuse to start without gVisor.

## 5. Sandbox and grading

Every Run and Submit gets a fresh container that is deleted when the job ends.

| Setting | Run | Submit |
| --- | --- | --- |
| CPU | 1 core | 1 core |
| Memory | 2 GB | 2 GB |
| Time limit | 30 s | 120 s |
| Network | Mock LLM only | Mock LLM only |
| Disk | Read-only image; 200 MB writable /tmp (proposed) | Same |
| Processes | 64 max (proposed) | Same |
| Tests | Sample tests from the statement | Hidden tests plus metric thresholds |
| Output shown to the user | stdout and stderr, first 64 KB (proposed) | Test names, author-written messages and metrics only |

Hardening: gVisor runtime; non-root user; all Linux capabilities dropped; no-new-privileges; an internal Docker network shared only with the mock LLM; task image pinned by digest; task data mounted read-only; no secrets inside the container.

Verdicts:

- `passed`: all hidden tests pass and every metric meets its threshold
- `failed`: at least one test or metric misses
- `error`: the code raised an exception or failed to import
- `time_limit`: hit the 30 s or 120 s limit
- `memory_limit`: went over 2 GB
- `system_error`: our fault (worker crash, image problem, or more than 5 minutes in the queue); refunded and not counted

Known limit: grading runs in the same process as user code, so a determined user could fake a pass. That's acceptable at MVP because there are no rankings. Keep the grader behind an interface so it can move to a separate process later.

### Mock LLM

An OpenAI-compatible HTTP service with chat-completion and embedding routes, so solutions look like production code. A prompt that matches the task's fixtures gets its recorded answer; anything else gets a fixed fallback. Embeddings come from precomputed vectors in the fixtures. It logs every call per job, so graders can check things like whether retrieved context reached the prompt.

### Task package

Each task is one folder in `/problems`:

```yaml
id: rag-chunking-01
title: Fix the chunking in a RAG pipeline
category: rag            # rag | training | evals | serving
difficulty: medium       # easy | medium | hard
est_minutes: 45
access: free             # free | paid
image: zagoat-py311-ml   # pinned by digest at deploy
files:
  statement: statement.md
  starter: starter/
  data: data/            # synthetic or licensed only
  hints: hints.md
  walkthrough: walkthrough.md   # paid users only
  reference: reference/         # shown after the first Submit
grader:
  sample_tests: tests/sample/   # used by Run
  hidden_tests: tests/hidden/   # used by Submit; never leaves the runner
  metrics:
    - name: recall_at_5
      threshold: 0.80
mock_llm: fixtures/llm.jsonl
```

CI rejects a task unless its reference solution passes its own hidden tests within the Submit limits. An API command syncs the public parts (metadata, statement, starter code, hints, walkthrough, reference) to Postgres; hidden tests and fixtures ship only to the runner.

## 6. Data model (Postgres)

| Table | Key fields |
| --- | --- |
| users | id, email, name, avatar_url, code_opt_in (default false), created_at, deleted_at |
| oauth_accounts | user_id, provider, provider_user_id |
| sessions | id, user_id, expires_at |
| problems | id (slug), title, category, difficulty, est_minutes, access, version, published, statement, starter_files, hints, walkthrough, reference_files |
| drafts | user_id, problem_id, files (JSON), updated_at |
| submissions | id, user_id, problem_id, problem_version, kind (run or submit), files (JSON), status (queued, running, done), verdict, tests_passed, tests_total, results (JSON), metrics (JSON), duration_ms, counted, created_at |
| progress | user_id, problem_id, state, hints_revealed, first_submit_at, solved_at, timer_seconds |
| subscriptions | id, user_id, provider, provider_ref, plan (pro_monthly, pro_yearly, lifetime), status, current_period_end, created_at |
| webhook_events | provider_event_id (unique), type, received_at, processed_at |
| usage_daily | user_id, day (UTC), submits |
| waitlist | email, source, consent, created_at |
| paths | id (slug), title, summary, position, task_ids (JSON, ordered) |

Plan definitions and limits live in config, not in the database.

## 7. API routes

| Route | Who can call it | What it does |
| --- | --- | --- |
| GET /auth/{github or google}/start and /callback | Anyone | OAuth sign-in; creates the user on first login |
| POST /auth/logout | Signed in | Ends the session |
| GET /me | Signed in | Profile, plan, today's usage and reset time |
| DELETE /me | Signed in | Deletes the account and its code, drafts and history |
| GET /problems | Anyone | List with category, difficulty, access and the user's progress |
| GET /problems/featured | Anyone | Landing-page previews from each task's `featured` block |
| GET /problems/{id} | Anyone | Statement; starter code needs access to the problem |
| POST /problems/{id}/hints/{n} | Users with access | Reveals the next hint and records it |
| GET /problems/{id}/walkthrough | Lifetime and Pro | Full written walkthrough |
| GET /problems/{id}/reference | Users who submitted once | Reference solution |
| PUT /problems/{id}/draft | Users with access | Autosave, debounced in the browser |
| POST /problems/{id}/runs | Users with access | Checks limits, queues a Run, returns a job id |
| POST /problems/{id}/submissions | Users with access | Checks the daily limit, queues a Submit, returns a job id |
| GET /paths and /paths/{id} | Anyone | Paths with their tasks in order, plus the user's progress and next task |
| GET /jobs/{id} | Job owner | Status and result |
| GET /problems/{id}/submissions | Owner | Submission history for one problem |
| POST /billing/checkout | Signed in | Creates a hosted checkout for Pro or Lifetime |
| GET /billing/portal | Paying users | Link to the provider's portal to cancel or update a card |
| POST /webhooks/payments | Payment provider | Signature-checked, idempotent billing updates |
| POST /waitlist | Anyone | Landing page signup; rate-limited per IP |
| POST /internal/jobs/{id}/result | Worker only | Result upload; shared secret plus IP allowlist |

## 8. Plans and entitlements

- Free: about 3 free problems at launch.
- Lifetime: one-time purchase, first 100 buyers only, price set in config.
- Pro: about $15 a month or $99 a year, behind the feature flag `PRO_SUBSCRIPTIONS_ENABLED`, which stays off until the library reaches about 20 problems.
- Lifetime and Pro unlock the same things; they differ only in how they are paid.

| Capability | Visitor | Free | Lifetime and Pro |
| --- | --- | --- | --- |
| Browse problems and read statements | Yes | Yes | Yes |
| Editor, Run and Submit on free problems | Sign in first | Yes | Yes |
| Editor, Run and Submit on paid problems | No | No | Yes |
| Hints | No | On free problems | Yes |
| Walkthroughs | No | No | Yes |
| Reference solution | No | After first Submit | After first Submit |
| Submission history | No | Yes | Yes |

Paid problem statements stay public, so search engines and visitors can see what they would unlock.

Access rule: a user has paid access if they hold an unrefunded lifetime purchase, or a Pro subscription that is active, past due within its grace period, or canceled but not yet at its period end. Everyone else is on Free. Compute this from the subscriptions table on each request; don't store a separate flag.

## 9. Limits and quotas

The API checks every limit before a job is queued.

| Limit | Free | Lifetime and Pro | Enforced in |
| --- | --- | --- | --- |
| Submits per day | 10 | 100 fair use (proposed) | usage_daily table |
| Runs per hour | 30 (proposed) | 120 (proposed) | Redis counter |
| Jobs in flight | 1 | 1 | Open-job check |
| Draft size | 1 MB (proposed) | 1 MB (proposed) | API validation |
| Time in queue | 5 min max | 5 min max | Worker drops older jobs as system_error |
| Sign-in and waitlist attempts | 5 per IP per hour (proposed) | Same | Redis counter |

- Days reset at 00:00 UTC; the UI shows the reset in the user's local time.
- A Submit counts when it is queued and is refunded if it ends in `system_error`.
- Runs never count toward the daily Submit limit.
- How many jobs run at once is a config value set by the runner's memory; at 2 GB per job, an 8 GB server runs about 3.
- Show remaining Submits and the reset time on the problem page; Free users also see an upgrade link when they hit a limit.

## 10. Billing

Write a `PaymentProvider` interface with `create_checkout(user, plan)`, `portal_url(user)`, `verify_webhook(request)`, `parse_event(payload)` and `fetch_subscription(ref)`. Ship a `FakeProvider` for local dev and tests. Add the real adapter when the provider is chosen.

Subscription states and what moves them:

| Event | New status | Access |
| --- | --- | --- |
| Subscription checkout completed | active, with the period end stored | Paid from now |
| Lifetime purchase completed | active, with plan lifetime and no period end | Paid, no end date |
| Renewal paid | active, period end moved forward | Continues |
| Payment failed | past_due | Kept for a 7-day grace period (proposed) |
| Subscription canceled | canceled | Kept until the period end |
| Subscription resumed | active | Continues |
| Subscription ended, or grace period over | expired | Back to Free |
| Refund or chargeback | refunded | Removed at once |

Webhook rules:

- Verify the signature, then record the event id in `webhook_events`. A repeated id is acknowledged and skipped.
- On every event, fetch the subscription's current state from the provider and save that, so events arriving out of order can't leave a wrong status.
- Reply 200 quickly; if processing fails, let the provider retry.
- Stop offering Lifetime once 100 are sold. If a sale lands after that, honor it (proposed).
- A nightly job compares paid users with the provider and fixes any drift.

## 11. Progress, unlocks and accounts

| Rule | Behavior |
| --- | --- |
| Progress states | not_started → in_progress (first draft save or Run) → attempted (first Submit) → solved (a Submit passes) |
| Solved is permanent | A later failing Submit or a new problem version never removes it |
| Reference solution | Unlocks after the first Submit with any verdict except system_error |
| Hints | Revealed one at a time; reveals are recorded but carry no penalty |
| Walkthroughs | Paid users can open them any time; the page warns that it shows the solution |
| Timer mode | Optional; records time to Submit and never changes the verdict |
| Problem versions | Each submission stores the version it ran against, so history shows old results as they were |
| Downgrade to Free | Drafts, history and solved states stay; paid problems become read-only |
| Account deletion | Self-service; removes the user, drafts, submissions and progress at once; backups age out within 30 days (proposed); billing records stay with the payment provider |
| Use of user code | Only for grading, unless the user opts in |

## 12. Pages and design

Pages: landing (`/`), tasks (`/tasks`: paths grid, and `/tasks/all`: every task in a table), path (`/paths/[id]`), task (`/tasks/[id]`), history (`/history`), pricing (`/pricing`), account (`/account`), sign-in (`/signin`), privacy (`/privacy`), terms (`/terms`) and a 404 page. Old `/problems` links redirect to `/tasks`.

Users see "tasks" everywhere (decided 2026-10-22). The API, database and the `problems/` folder keep the internal name "problems".

Paths (decided 2026-10-22): a path is a named, ordered route through tasks, defined in `problems/paths.yaml` and validated in CI. `/tasks` shows the paths as a grid; picking one opens its page, and on a task opened from a path, previous and next follow that path. Path progress comes from task progress; there is no separate "join path" step.

- Landing: the 3D hero, then 2–3 real sample tasks as read-only previews (free tasks only, picked by the `featured` block in their `problem.yaml`, decided 2026-10-22), pricing, and a waitlist form (email plus consent checkbox). The privacy page must be live before the waitlist collects any email.
- Privacy and terms: simple placeholder text, clearly marked for my review before launch.

All UI work follows the project skill in `.claude/skills/zagoat-design/SKILL.md` (you can also run it with `/zagoat-design`), together with Anthropic's `frontend-design` skill when it's installed. The skill holds the full design rules. The essentials:

- The logo at `web/public/brand/logo.png` is used as-is, and the color palette is built from it. The old indigo and lime palette is retired.
- LeetCode is a reference for layout and flow only; never copy its look, assets or wording.
- The landing page has a 3D hero, with a static fallback for reduced motion, missing WebGL and phones.
- Show a design plan and wait for my OK before building, and share screenshots in both themes when done.

## 13. Security checklist

- CSRF protection on every state-changing route (SameSite cookies plus a CSRF token)
- CORS limited to the web app's origin
- Rate limits from section 9
- Webhook signatures verified; webhook handling idempotent
- Internal routes protected by a shared secret and an IP allowlist
- Hidden tests and fixtures never appear in API responses or the web bundle
- Store the minimum personal data: email, name, avatar; payment details stay with the provider
- Dependencies pinned, with automated update checks

## 14. Milestones

Every milestone ends with tests passing, lint clean, the README updated, and a summary that lists your assumptions. Then stop and wait for review.

1. Foundations: monorepo layout, docker-compose (Postgres, Redis), FastAPI and Next.js skeletons, config modules, `.env.example`, CI for lint and tests, README with run instructions.
2. Landing page and waitlist: design plan first, then the landing page, waitlist API and table, privacy and terms pages, analytics and Sentry. This must be deployable on its own so I can start validation early.
3. Accounts: GitHub and Google OAuth, sessions, `/me`, account page, self-service deletion.
4. Problems: problem.yaml schema and loader, sync command, CI task validation, problem list and statement pages, and two original sample tasks (one RAG, one evals) with sample tests, hidden tests, data, hints and reference solutions. These are for development; I'll write the launch tasks.
5. Editor and drafts: Monaco editor, file tabs for multi-file tasks, debounced autosave.
6. Runner: worker, sandbox with every limit and hardening rule, mock LLM, Run and Submit end to end, verdicts, results panel, polling, queue timeout.
7. Business rules: entitlements, limits and counters, progress states, unlocks (hints, walkthroughs, reference), history page, timer, downgrade behavior.
8. Billing: PaymentProvider interface and FakeProvider, checkout, portal, webhooks, subscription states, Lifetime cap, pricing page, Pro feature flag, nightly reconciliation.
9. Production: Vercel deploy, setup scripts for both servers, gVisor install, firewall rules, TLS, nightly backups with a tested restore, and a short runbook.

## 15. Open decisions

Use these defaults and keep each one easy to change.

| Decision | Default until decided |
| --- | --- |
| Payment provider | FakeProvider |
| Lifetime price | Config value, unset |
| Paid fair-use caps | 100 Submits a day, 120 Runs an hour |
| Free Runs per hour | 30 |
| Runner server size | 8 GB RAM, about 3 jobs at once |
| Grace period for failed payments | 7 days |
| Backup retention after deletion | 30 days |
| Pro subscriptions | Flag off until about 20 problems exist |
