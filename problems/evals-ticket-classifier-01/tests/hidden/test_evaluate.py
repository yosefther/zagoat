import pytest

from eval import evaluate

LABELS = ["billing", "bug", "account", "feature_request", "other"]


def test_report_shape():
    """The report has exactly the documented keys"""
    report = evaluate(["bug"], ["bug"])
    assert set(report) == {"accuracy", "macro_f1", "per_label", "unparseable", "never_predicted"}, (
        "The report should have exactly the keys listed in the statement"
    )
    assert list(report["per_label"]) == LABELS, "per_label should list every label, in order"


def test_scores_a_small_mixed_case():
    """Per-label precision, recall and F1 on a small mixed case"""
    report = evaluate(["billing", "billing", None, "bug"], ["billing", "bug", "bug", "account"])
    billing = report["per_label"]["billing"]
    assert billing["precision"] == pytest.approx(0.5), "billing precision is off"
    assert billing["recall"] == pytest.approx(1.0), "billing recall is off"
    assert billing["f1"] == pytest.approx(2 / 3), "billing F1 is off"
    assert report["per_label"]["bug"] == {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 2}, (
        "bug was predicted once and wrongly, so its scores should all be 0"
    )
    assert report["accuracy"] == pytest.approx(0.25), "accuracy is off"


def test_unparseable_replies_count_as_wrong():
    """None predictions are counted and never match a gold label"""
    report = evaluate([None, None, "bug"], ["bug", "bug", "bug"])
    assert report["unparseable"] == 2, "unparseable should count the None predictions"
    assert report["accuracy"] == pytest.approx(1 / 3), "None predictions should count as wrong"
    assert report["per_label"]["bug"]["recall"] == pytest.approx(1 / 3), "bug recall is off"


def test_no_division_by_zero():
    """Labels that are never predicted or never present score 0 instead of crashing"""
    report = evaluate(["bug"], ["billing"])
    for label in LABELS:
        row = report["per_label"][label]
        assert row["precision"] == 0.0 and row["recall"] == 0.0 and row["f1"] == 0.0, (
            "A label with no correct predictions should score 0, not raise or return NaN"
        )


def test_macro_f1_averages_every_label():
    """macro_f1 averages F1 over all five labels"""
    report = evaluate(["billing", "billing", None, "bug"], ["billing", "bug", "bug", "account"])
    assert report["macro_f1"] == pytest.approx((2 / 3) / 5), (
        "macro_f1 should be the plain mean of F1 over all five labels"
    )


def test_never_predicted_lists_missing_labels_in_order():
    """never_predicted lists labels the model never chose"""
    report = evaluate(["billing", "billing", None, "bug"], ["billing", "bug", "bug", "account"])
    assert report["never_predicted"] == ["account", "feature_request", "other"], (
        "never_predicted should list, in label order, every label that was never predicted"
    )
