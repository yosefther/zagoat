"""Evaluate the ticket classifier. Fill in the three functions below."""

import json
import re

from openai import OpenAI

from classifier import classify
from prompts import LABELS
from zagoat import data_path

# Each label as a whole phrase; "feature_request" also matches "feature request".
LABEL_PATTERNS = {
    label: re.compile(r"\b" + label.replace("_", r"[\s_-]") + r"\b") for label in LABELS
}


def parse_label(reply: str) -> str | None:
    """Turn a raw model reply into one of LABELS, or None if it names zero or several labels."""
    text = reply.lower()
    found = [label for label, pattern in LABEL_PATTERNS.items() if pattern.search(text)]
    return found[0] if len(found) == 1 else None


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def evaluate(predictions: list[str | None], gold: list[str]) -> dict:
    """Score predictions against gold labels. See the statement for the report's shape."""
    if len(predictions) != len(gold):
        raise ValueError("predictions and gold must have the same length")
    per_label = {}
    for label in LABELS:
        tp = sum(p == label and g == label for p, g in zip(predictions, gold, strict=True))
        predicted = sum(p == label for p in predictions)
        support = sum(g == label for g in gold)
        precision = _ratio(tp, predicted)
        recall = _ratio(tp, support)
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_label[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }
    correct = sum(p == g for p, g in zip(predictions, gold, strict=True))
    return {
        "accuracy": _ratio(correct, len(gold)),
        "macro_f1": sum(row["f1"] for row in per_label.values()) / len(LABELS),
        "per_label": per_label,
        "unparseable": sum(p is None for p in predictions),
        "never_predicted": [label for label in LABELS if label not in predictions],
    }


def run_eval(client: OpenAI, tickets: list[dict]) -> dict:
    """Classify every ticket with the model, parse the replies and return the report."""
    predictions = [parse_label(classify(client, ticket["text"])) for ticket in tickets]
    return evaluate(predictions, [ticket["label"] for ticket in tickets])


def load_tickets() -> list[dict]:
    return [json.loads(line) for line in data_path("tickets.jsonl").read_text().splitlines()]


if __name__ == "__main__":
    report = run_eval(OpenAI(), load_tickets())
    print(json.dumps(report, indent=2))
    print("Labels:", ", ".join(LABELS))
