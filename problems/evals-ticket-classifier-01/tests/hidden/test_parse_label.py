import pytest

from eval import parse_label

CASES = [
    ("account", "account"),
    ("  ACCOUNT\n", "account"),
    ("Billing.", "billing"),
    ("I'd say this is a billing issue.", "billing"),
    ("feature-request", "feature_request"),
    ("feature_request", "feature_request"),
    ("Answer: other", "other"),
    ("This is either a bug or an account problem.", None),
    ("Could be billing, could be account.", None),
    ("No label fits this well.", None),
    ("", None),
]


@pytest.mark.parametrize(("reply", "expected"), CASES)
def test_parse_label(reply, expected):
    """parse_label maps messy replies to one label, or None"""
    assert parse_label(reply) == expected, (
        "parse_label should return the single label a reply names, and None when it names "
        "zero or several labels"
    )
