import json

import pytest
from openai import OpenAI

from eval import run_eval
from zagoat import data_path, llm_calls


@pytest.fixture(scope="module")
def tickets():
    return [json.loads(line) for line in data_path("tickets.jsonl").read_text().splitlines()]


@pytest.fixture(scope="module")
def report(tickets):
    return run_eval(OpenAI(), tickets)


def test_full_eval_numbers(report):
    """End-to-end eval on the ticket set gives the right numbers"""
    assert report["accuracy"] == pytest.approx(25 / 38), "accuracy on the full set is off"
    assert report["macro_f1"] == pytest.approx(0.618333, abs=1e-5), "macro_f1 on the full set is off"
    assert report["unparseable"] == 4, "unparseable count on the full set is off"
    assert report["never_predicted"] == ["other"], "never_predicted on the full set is off"
    account = report["per_label"]["account"]
    assert account["precision"] == pytest.approx(0.6), "account precision on the full set is off"


def test_asks_the_model_once_per_ticket(report, tickets):
    """run_eval asks the model exactly once per ticket"""
    chats = [call for call in llm_calls() if call["endpoint"] == "chat.completions"]
    assert len(chats) == len(tickets), "Each ticket should be classified exactly once"
