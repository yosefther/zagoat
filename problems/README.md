# problems

One folder per practice task. The folder name is the task id. Tasks must be original
(never copied interview questions), and data must be synthetic or clearly licensed.

## Layout

```
<id>/
  problem.yaml        metadata, grading and file locations (schema below)
  statement.md        what the user reads
  starter/            files the user edits; every file opens as an editor tab
  reference/          the solution: only the starter files it changes
  data/               read-only data, read with zagoat.data_path(...)
  hints.md            "## Hint 1", "## Hint 2", ... revealed one at a time
  walkthrough.md      full solution write-up, paid users only
  tests/sample/       run by "Run tests"; visible to users through their output
  tests/hidden/       run by "Submit solution"; never leaves the runner
  fixtures/llm.jsonl  optional recorded mock-LLM replies
```

## problem.yaml

The schema lives in `api/app/problems/schema.py`. Unknown keys are rejected.

```yaml
id: rag-chunking-01          # must match the folder name
title: Fix the chunking in a RAG pipeline
summary: One or two sentences for the problem list.
category: rag                # rag | training | evals | serving
difficulty: medium           # easy | medium | hard
est_minutes: 45
access: free                 # free | paid
published: true              # optional; false hides the task
image: zagoat-py311-ml
files:                       # optional; these are the defaults
  statement: statement.md
  starter: starter/
  data: data/
  hints: hints.md
  walkthrough: walkthrough.md
  reference: reference/
grader:
  sample_tests: tests/sample/
  hidden_tests: tests/hidden/
  metrics:
    - name: recall_at_5
      threshold: 0.80
      goal: at_least         # optional; at_most for latency-style metrics
mock_llm: fixtures/llm.jsonl # optional
```

## Writing tests

Tests are plain pytest files that import the user's modules by name (`from chunker import
...`). Helper modules can sit next to the tests (for example `rag_helpers.py`); give them
names that won't clash with starter files.

- **Messages:** for hidden tests users see the test's docstring (or its name) and the
  assertion message you write, nothing else. Always write `assert x, "what went wrong"`.
- **Metrics:** call `zagoat.record_metric("recall_at_5", value)` in a test. The grader
  compares it with the threshold in `problem.yaml`; a missing metric counts as a miss.
- **Mock LLM:** the OpenAI client works out of the box (`OpenAI()` reads
  `OPENAI_BASE_URL` and `OPENAI_API_KEY`). `zagoat.llm_calls()` returns every call this job
  made, so tests can check what reached the prompt.

## Mock LLM fixtures

`fixtures/llm.jsonl`, one JSON object per line:

```json
{"kind": "chat", "user": "<last user message>", "response": "<assistant reply>"}
{"kind": "embedding", "input": "<text>", "vector": [0.1, 0.2]}
```

A chat request whose last user message matches (whitespace collapsed) gets the recorded
reply; anything else gets a fixed fallback. Embeddings without a recorded vector come from a
deterministic hashed bag of words (256 dimensions), so texts that share words land close
together.

## Checking a task

```sh
cd api && uv run python -m app.problems validate ../problems    # schema and files
cd runner && uv run python -m zagoat_runner.validate ../problems  # grading
```

The second command checks that the reference passes the hidden tests within the Submit time
limit and passes the sample tests, that the untouched starter does not pass, and that broken
code gets the `error` verdict. CI runs both on every push.

To load tasks into your local database, run `cd api && uv run python -m app.problems sync`.
Any change to a task folder, hidden tests included, bumps its version. Tasks removed from
the folder are unpublished, not deleted.
