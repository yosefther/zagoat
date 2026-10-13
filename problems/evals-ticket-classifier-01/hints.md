# Hints

## Hint 1

Lowercase the reply first, then look for each label with a regular expression and word
boundaries (`\b`). Collect every label you find and only return one if exactly one matched.

## Hint 2

Precision for a label is "of the times we predicted it, how often was it right"; recall is
"of the tickets that really had it, how many did we catch". Count true positives, predicted
and actual for each label, and guard every division.

## Hint 3

`None` predictions still belong in the totals. They lower accuracy and recall, but they never
count as a prediction of any label.
