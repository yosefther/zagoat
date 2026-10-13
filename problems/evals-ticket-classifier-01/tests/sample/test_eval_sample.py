"""Sample tests. Run them as often as you like; Submit runs a larger hidden set."""

import pytest

from eval import evaluate, parse_label


@pytest.mark.parametrize(
    ("reply", "expected"),
    [
        ("billing", "billing"),
        ("Label: bug", "bug"),
        ("Feature request", "feature_request"),
        ("I'm not sure.", None),
    ],
)
def test_parse_label(reply, expected):
    assert parse_label(reply) == expected


def test_perfect_predictions():
    report = evaluate(["bug", "billing"], ["bug", "billing"])
    assert report["accuracy"] == 1.0
    assert report["per_label"]["bug"] == {"precision": 1.0, "recall": 1.0, "f1": 1.0, "support": 1}
