"""Evaluate the ticket classifier. Fill in the three functions below."""

import json

from openai import OpenAI

from classifier import classify
from prompts import LABELS
from zagoat import data_path


def parse_label(reply: str) -> str | None:
    """Turn a raw model reply into one of LABELS, or None if it names zero or several labels."""
    raise NotImplementedError


def evaluate(predictions: list[str | None], gold: list[str]) -> dict:
    """Score predictions against gold labels. See the statement for the report's shape."""
    raise NotImplementedError


def run_eval(client: OpenAI, tickets: list[dict]) -> dict:
    """Classify every ticket with the model, parse the replies and return the report."""
    raise NotImplementedError


def load_tickets() -> list[dict]:
    return [json.loads(line) for line in data_path("tickets.jsonl").read_text().splitlines()]


if __name__ == "__main__":
    report = run_eval(OpenAI(), load_tickets())
    print(json.dumps(report, indent=2))
    print("Labels:", ", ".join(LABELS))
