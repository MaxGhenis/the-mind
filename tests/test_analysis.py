import pytest

from themind.analysis import paired_contrast, summarize, wilson


def row(condition, seed, status, hands=None):
    return dict(
        condition=condition,
        seed=seed,
        status=status,
        hands=hands or [[1], [2]],
        correct_prefix=0,
        collisions=0,
    )


def test_failures_are_not_silently_excluded():
    result = summarize([row("a", 1, "success"), row("a", 2, "invalid_response")])["a"]
    assert result["valid"] == 1
    assert result["completion_rate_all_attempts"] == 0.5
    assert result["completion_rate_valid_only"] == 1
    assert result["infrastructure_failure_rate"] == 0.5


def test_no_valid_rounds():
    result = summarize([row("a", 1, "provider_error")])["a"]
    assert result["completion_ci95_valid_only"] is None
    assert wilson(0, 0) is None
    assert wilson(0, 10)[0] == pytest.approx(0)
    assert wilson(10, 10)[1] == pytest.approx(1)


def test_pairing_does_not_depend_on_record_order():
    rows = [
        row("b", 2, "misorder"),
        row("a", 1, "success"),
        row("b", 1, "misorder"),
        row("a", 2, "success"),
    ]
    result = paired_contrast(rows, {"a": 1, "b": -1}, bootstrap_samples=100)
    assert result["difference_all_attempts"] == 1
    assert result["paired_bootstrap_ci95"] == [1, 1]


@pytest.mark.parametrize(
    "rows",
    [
        [row("a", 1, "success")],
        [row("a", 1, "success"), row("b", 1, "success", [[3], [4]])],
        [row("a", 1, "success"), row("a", 1, "success"), row("b", 1, "success")],
    ],
)
def test_bad_pairing_rejected(rows):
    with pytest.raises(ValueError):
        paired_contrast(rows, {"a": 1, "b": -1})
