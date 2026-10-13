# Walkthrough

This shows the full solution. Try the hints first if you'd like to solve it yourself.

## Parsing replies

One regular expression per label handles case, punctuation and the `feature_request`
spellings. Requiring exactly one match turns hedged answers like "either a bug or an account
problem" into `None` instead of guessing:

```python
LABEL_PATTERNS = {
    label: re.compile(r"\b" + label.replace("_", r"[\s_-]") + r"\b") for label in LABELS
}


def parse_label(reply):
    text = reply.lower()
    found = [label for label, pattern in LABEL_PATTERNS.items() if pattern.search(text)]
    return found[0] if len(found) == 1 else None
```

## Metrics

Count per label, then derive the ratios with a guard for empty denominators:

```python
for label in LABELS:
    tp = sum(p == label and g == label for p, g in zip(predictions, gold))
    predicted = sum(p == label for p in predictions)
    support = sum(g == label for g in gold)
    precision = tp / predicted if predicted else 0.0
    recall = tp / support if support else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
```

`macro_f1` is the mean over all five labels, so a label the model never predicts pulls it
down. That's the point: on this data the model never says `other`, and macro F1 (0.62) is
much lower than accuracy (0.66) suggests.

## What the eval tells you

- `other` has 7 tickets and is never predicted; the model forces off-topic tickets into a
  team's queue. That's a routing bug worth fixing before launch.
- 4 replies are unparseable. Constraining the output (a JSON schema or a short list of
  allowed answers) usually fixes that.

## In an interview

Talk about what you'd add next: a confusion matrix, confidence intervals for a set this
small, a frozen eval set checked into the repo, and tracking these numbers across prompt or
model changes.
