Tidepool, a (fictional) note-taking app, uses an LLM to label incoming support tickets as
`billing`, `bug`, `account`, `feature_request` or `other`. The labels route tickets to teams,
but nobody has measured how good they are. Write the eval.

`classifier.py` already calls the model and returns its raw reply. Replies don't always
follow the format: you'll see `Billing.`, `Label: bug`, `feature-request`, full sentences
and the occasional shrug.

## What to build in `eval.py`

**`parse_label(reply)`** returns the one label a reply names, or `None`.

- Matching ignores case. A label counts only as a whole word; `feature_request` also matches
  `feature request` and `feature-request`.
- If a reply names no label, or more than one, return `None`.

**`evaluate(predictions, gold)`** returns a report dict with exactly these keys:

| Key | Meaning |
| --- | --- |
| `accuracy` | Share of predictions equal to the gold label. `None` counts as wrong. |
| `per_label` | For every label in `LABELS`, in order: `precision`, `recall`, `f1`, `support` |
| `macro_f1` | Plain mean of `f1` over all five labels |
| `unparseable` | Number of `None` predictions |
| `never_predicted` | Labels that never appear in `predictions`, in `LABELS` order |

When a ratio would divide by zero, use `0.0`.

**`run_eval(client, tickets)`** classifies each ticket once with `classify`, parses the
replies and returns `evaluate(...)` on them.

## Data

`data/tickets.jsonl` holds 38 labelled tickets. The model is mocked with recorded replies,
so keep using `build_prompt` from `prompts.py` unchanged; a different prompt gets a generic
answer.

## How you're graded

**Run tests** runs the sample tests. **Submit solution** runs hidden tests on parsing, on
the metric definitions above, including edge cases, and on the full eval over the ticket set.
