import json
from pathlib import Path

import pytest

from themind.timing import build_plan, digest
from themind.timing_analysis import (
    cell_stats,
    free_policy_curves,
    paired_contrasts,
    paired_effect,
    representation_agreement,
    summarize,
)
from themind.timing_controls import control_response, descriptor
from themind.timing_runner import attempt_record, derive_rows, result_record


def protocol():
    p = json.loads(Path("experiments/stage1-pilot.json").read_text())
    p.update(repetitions=1, free_repetitions=3)
    return p


def rows_for(name, p=None, change=None):
    p = p or protocol()
    plan = build_plan(p)
    participant = descriptor(name)
    manifest = {
        "run_id": "offline-test",
        "participant": participant,
        "participant_sha256": digest(participant),
        "protocol_sha256": digest(p),
        "source_kind": "deterministic_offline_control",
    }
    attempts, results = [], []
    for probe in plan:
        a = attempt_record(manifest, probe, "2026-09-07T20:00:00Z")
        response = control_response(name, probe["request"], probe["repetition"])
        if change:
            change(response, probe)
        attempts.append(a)
        results.append(result_record(a, response, "2026-09-07T20:00:00Z", 0))
    return derive_rows(manifest, plan, attempts, results), p, manifest


def test_positive_control_passes_every_prescribed_snapshot_transformation():
    rows, p, m = rows_for("oracle")
    summary = summarize(rows, p, m)
    c = summary["counts"]
    assert c["planned"] == c["valid"]
    assert c["compliant"] == c["external_target_valid"]
    assert c["mean_absolute_target_error_seconds"] == 0
    assert c["binary_decision_accuracy"] == 1
    assert all(s["agreement"] == 1 for s in summary["representation_agreement"])
    assert all(s["valid_only_case_mean_difference"] == 0 for s in summary["paired_contrasts"])
    for curve in summary["free_policy_curves"]:
        assert [point["q"] for point in curve["points"]] == [0, 1 / 3, 2 / 3, 1, 1]
        assert all(
            point["q_minus_F_absolute"] == 0 and point["q_minus_F_delay"] == 0
            for point in curve["points"]
        )
        assert curve["q_adjacent_decreases"] == 0
    never = summary["never_snapshot_sets"]
    assert (
        never["planned_snapshot_sets"] == never["correct_wait_at_every_snapshot_including_deadline"]
    )


def test_unit_fault_is_numerical_while_poll_decisions_remain_correct():
    rows, _, _ = rows_for("unit_blind")
    polls = cell_stats([r for r in rows if r["interface"] == "poll"])
    numeric = cell_stats([r for r in rows if r["interface"] != "poll"])
    assert polls["valid_only_compliance"] == 1
    assert polls["binary_decision_accuracy"] == 1
    assert numeric["valid_only_compliance"] < 1
    assert numeric["mean_absolute_target_error_seconds"] > 0
    comparisons = representation_agreement(rows)
    assert all(r["agreement"] == 1 for r in comparisons if r["interface"] == "poll")
    assert any(
        r["agreement"] < 1
        for r in comparisons
        if r["unit"] == "milliseconds" and r["interface"] == "delay"
    )


def test_poll_only_framing_fault_identified_without_numerical_errors():
    rows, _, _ = rows_for("poll_early")
    numeric = cell_stats([r for r in rows if r["interface"] != "poll"])
    assert numeric["valid_only_compliance"] == 1
    assert numeric["mean_absolute_target_error_seconds"] == 0
    contrasts = [r for r in paired_contrasts(rows) if r["contrast"] == "time_minus_magnitude"]
    assert any(
        r["valid_only_case_mean_difference"] < 0 for r in contrasts if r["interface"] == "poll"
    )
    assert all(
        r["valid_only_case_mean_difference"] == 0 for r in contrasts if r["interface"] != "poll"
    )


def test_arithmetic_fault_separate_from_retrieval_and_unit_conversion():
    rows, _, _ = rows_for("arithmetic_blind")
    assert (
        cell_stats([r for r in rows if r["snapshot"]["target_kind"] == "direct"])[
            "valid_only_compliance"
        ]
        == 1
    )
    assert (
        cell_stats([r for r in rows if r["snapshot"]["target_kind"] == "computed"])[
            "valid_only_compliance"
        ]
        < 1
    )
    contrasts = [r for r in paired_contrasts(rows) if r["contrast"] == "computed_minus_direct"]
    assert any(r["valid_only_case_mean_difference"] < 0 for r in contrasts)


def test_origin_fault_detected_for_absolute_only():
    rows, _, _ = rows_for("origin_blind")
    assert (
        cell_stats([r for r in rows if r["interface"] != "absolute"])["valid_only_compliance"] == 1
    )
    assert (
        cell_stats(
            [r for r in rows if r["interface"] == "absolute" and r["representation"]["origin"] == 0]
        )["valid_only_compliance"]
        == 1
    )
    assert (
        cell_stats(
            [
                r
                for r in rows
                if r["interface"] == "absolute" and r["representation"]["origin"] == 137
            ]
        )["valid_only_compliance"]
        < 1
    )


@pytest.mark.parametrize("name", ["always_play", "always_wait"])
def test_constant_controls_differentiate_never_due_false_activation_and_missed_due(name):
    rows, p, m = rows_for(name)
    summary = summarize(rows, p, m)
    never = summary["never_snapshot_sets"]
    if name == "always_play":
        assert never["sets_with_false_activation"] == never["planned_snapshot_sets"]
        assert never["correct_wait_at_every_snapshot_including_deadline"] == 0
    else:
        assert never["sets_with_false_activation"] == 0
        assert (
            never["correct_wait_at_every_snapshot_including_deadline"]
            == never["planned_snapshot_sets"]
        )
        assert summary["counts"]["wait_when_due"] > 0
    assert summary["instrument_checks"]["all_prescribed_snapshots_compliant"] is False


def test_paired_effect_weights_cases_not_individual_snapshots():
    def row(case, correct, status="valid"):
        return {"snapshot": {"case": case}, "status": status, "score": {"compliant": correct}}

    pairs = [(row("many", True), row("many", False))] * 9 + [(row("one", False), row("one", True))]
    result = paired_effect(pairs)
    assert result["valid_only_case_mean_difference"] == 0  # pooled probes would be +0.8
    assert result["case_differences"] == {"many": 1, "one": -1}
    assert result["independent_case_count"] == 2
    result = paired_effect([(row("a", True), row("a", None, "provider_error"))])
    assert result["all_attempt_case_mean_difference"] == 1
    assert result["valid_only_case_mean_difference"] is None
    assert result["both_valid"] == 0


def test_free_cdf_keeps_null_and_future_mass_and_exposes_independent_q_gap():
    p = protocol()
    p.update(units=["seconds"], directions=["elapsed"], origins=[0], free_repetitions=4)
    p["cases"] = [p["cases"][-1]]
    p["cases"][0]["times"] = [0, 15, 30]

    def change(response, probe):
        if probe["interface"] == "poll":
            # Independent snapshot q=.75, irrespective of proposed plan samples.
            response["raw_text"] = json.dumps({"play": probe["repetition"] < 3})
        else:
            response["raw_text"] = json.dumps(
                {
                    "time" if probe["interface"] == "absolute" else "delay": [0, 15, 31, None][
                        probe["repetition"]
                    ]
                }
            )

    rows, _, _ = rows_for("oracle", p, change)
    curve = free_policy_curves(rows)[0]
    assert curve["plans"]["absolute"] == {
        "planned": 4,
        "valid_schedule_or_no_action": 4,
        "no_action": 1,
        "past_reference": 0,
        "after_deadline": 1,
    }
    assert [x["F_absolute"] for x in curve["points"]] == [0.25, 0.5, 0.5]
    assert [x["q"] for x in curve["points"]] == [0.75, 0.75, 0.75]
    assert [x["q_minus_F_absolute"] for x in curve["points"]] == [0.5, 0.25, 0.25]
    assert all(r["score"]["compliant"] is None for r in rows)
    assert (
        representation_agreement(rows) == []
    )  # stochastic free samples are not paired equality tests


def test_valid_unexpected_terminal_is_wrong_decision_not_dropped_observation():
    def change(response, probe):
        response["raw_text"] = '{"terminal":"deadline_missed"}'

    rows, _, _ = rows_for("oracle", change=change)
    selected = [
        r
        for r in rows
        if r["snapshot"]["target_kind"] in {"direct", "computed"} and r["snapshot"]["now"] <= 30
    ]
    assert selected and all(r["score"]["decision_correct"] is False for r in selected)
    assert cell_stats(selected)["binary_decision_accuracy"] == 0


def test_no_due_schedule_after_endpoint_is_contract_error_not_in_window_activation():
    def change(response, probe):
        if probe["interface"] == "absolute":
            response["raw_text"] = '{"time":10000}'

    p = protocol()
    p.update(units=["seconds"], origins=[0])
    rows, _, _ = rows_for("oracle", p, change)
    never = [
        r for r in rows if r["snapshot"]["target_kind"] == "never" and r["interface"] == "absolute"
    ]
    assert all(r["score"]["compliant"] is False for r in never)
    # Some countdown coordinates correspond to invalid past values; neither those
    # nor schedules beyond deadline are admissible in-window activations.
    assert all(r["score"]["false_activation"] is False for r in never)
