import copy
import json
from dataclasses import asdict

import pytest

from themind.timing import (
    Representation,
    Snapshot,
    build_plan,
    build_request,
    parse_response,
    score_response,
)


def state(now=10, target=20, kind="direct", deadline=30):
    return Snapshot("known", "held_out", now, deadline, target, kind)


@pytest.mark.parametrize("unit,scale", [("seconds", 1), ("milliseconds", 1000), ("ticks", 4)])
@pytest.mark.parametrize("direction", ["elapsed", "countdown"])
@pytest.mark.parametrize("origin", [0, 137, -40])
def test_known_coordinate_and_delay_normalize_to_same_physical_action(
    unit, scale, direction, origin
):
    s, r = state(), Representation(unit, direction, origin)
    # Hand-calculated fixture independent of coordinate()/seconds().
    expected_current = (origin + (10 if direction == "elapsed" else 20)) * scale
    expected_target = (origin + (20 if direction == "elapsed" else 10)) * scale
    for interface, response in (
        ("absolute", {"time": expected_target}),
        ("delay", {"delay": 10 * scale}),
        ("poll", {"play": False}),
    ):
        packet = build_request(s, r, interface)
        payload = json.loads(packet["user"])
        assert payload["current"] == expected_current
        assert payload["target"] == expected_target
        assert payload["endpoint"] == (origin + (30 if direction == "elapsed" else 0)) * scale
        assert set(packet) == {"prompt_version", "system", "user", "response_schema"}
        normalized = parse_response(json.dumps(response), interface, s, r)
        assert score_response(normalized, s, interface)["compliant"] is True
        if interface != "poll":
            assert normalized["time_seconds"] == 20


@pytest.mark.parametrize("now,expected", [(0, 20), (19.5, 20), (20, 20), (20.5, 20.5), (30, 30)])
def test_overdue_target_explicitly_becomes_act_now(now, expected):
    s = state(now=now)
    assert s.expected == ("schedule", expected)
    n = parse_response(json.dumps({"delay": expected - now}), "delay", s, Representation())
    assert score_response(n, s, "delay")["compliant"] is True
    for play in [False, True]:
        n = parse_response(json.dumps({"play": play}), "poll", s, Representation())
        assert score_response(n, s, "poll")["compliant"] == (play == (now >= 20))


@pytest.mark.parametrize("now", [0, 29.5, 30, 30.5])
@pytest.mark.parametrize("kind,target", [("never", None), ("direct", 31)])
@pytest.mark.parametrize(
    "interface,key,answer",
    [("absolute", "time", None), ("delay", "delay", None), ("poll", "play", False)],
)
def test_never_and_beyond_endpoint_are_correct_wait_not_timeout(
    now, kind, target, interface, key, answer
):
    s = state(now, target, kind)
    n = parse_response(json.dumps({key: answer}), interface, s, Representation())
    score = score_response(n, s, interface)
    assert score["expected"] == "no_action"
    assert score["correct_wait"] is True
    assert score["false_activation"] is False
    assert score["target_error_seconds"] is None


def test_terminal_not_forced_play_and_not_schema_failure():
    s = state(now=30.5)
    n = parse_response('{"terminal":"deadline_missed"}', "poll", s, Representation())
    assert n["time_seconds"] is None
    assert score_response(n, s, "poll")["compliant"] is True
    wrong = parse_response('{"play":true}', "poll", s, Representation())
    score = score_response(wrong, s, "poll")
    assert score["compliant"] is False
    assert score["after_deadline"] is True
    assert score["decision_correct"] is None


@pytest.mark.parametrize(
    "raw",
    [
        '{"time":true}',
        '{"time":"20"}',
        '{"time":NaN}',
        '{"time":1e400}',
        '{"time":20,"time":21}',
        '{"time":20,"extra":0}',
        '{"times":[20]}',
        '```json\n{"time":20}\n```',
        '{"terminal":"timeout"}',
        '{"time":',
        "[]",
        "null",
    ],
)
def test_malformed_outputs_are_never_repaired(raw):
    with pytest.raises(ValueError):
        parse_response(raw, "absolute", state(), Representation())


@pytest.mark.parametrize("raw", ['{"play":1}', '{"play":null}', '{"play":"false"}'])
def test_poll_requires_boolean(raw):
    with pytest.raises(ValueError):
        parse_response(raw, "poll", state(), Representation())


def test_valid_but_wrong_numbers_are_behavioral_not_invalid_schema():
    s, r = state(), Representation()
    n = parse_response('{"delay":-2}', "delay", s, r)
    assert n["time_seconds"] == 8  # no clamp
    score = score_response(n, s, "delay")
    assert score["past_schedule"] is True
    assert score["premature"] is True
    assert score["target_error_seconds"] == -12
    n = parse_response('{"time":40}', "absolute", s, r)
    score = score_response(n, s, "absolute")
    assert score["after_deadline"] is True
    assert score["target_error_seconds"] == 20
    assert score["decision_correct"] is True  # both choose not-now; numeric execution still wrong
    assert score["compliant"] is False


def test_free_preference_has_no_external_correctness():
    s = state(now=0, target=None, kind="free")
    n = parse_response('{"time":13}', "absolute", s, Representation())
    score = score_response(n, s, "absolute")
    assert score["compliant"] is None
    assert score["decision_correct"] is None
    assert score["external_target"] is False
    assert score["target_error_seconds"] is None


def test_computed_prompt_hides_target_and_scoring_state():
    s = Snapshot("hidden-case-id", "held_out", 10, 30, 20, "computed", 2, 10)
    packet = build_request(s, Representation("milliseconds", "countdown", 137), "absolute")
    payload = json.loads(packet["user"])
    assert payload == {
        "unit": "milliseconds",
        "direction_sign": -1,
        "reference": 167000,
        "current": 157000,
        "endpoint": 137000,
        "target_kind": "computed",
        "item": 2,
        "step_distance": 10000,
    }
    assert "hidden-case-id" not in json.dumps(packet)
    assert "held_out" not in json.dumps(packet)
    assert "target" not in payload
    assert "snapshot" not in payload


def test_neutral_magnitude_matched_structure():
    time = build_request(state(), Representation(), "poll")
    magnitude = build_request(state(), Representation(frame="magnitude"), "poll")
    t, m = json.loads(time["user"]), json.loads(magnitude["user"])
    assert t.pop("unit") == "seconds"
    assert m.pop("unit") == "units"
    assert t == m
    assert time["response_schema"] == magnitude["response_schema"]
    assert time["system"] != magnitude["system"]


def test_frozen_plan_randomized_uncensored_complete_and_bounded():
    from pathlib import Path

    p = json.loads(Path("experiments/stage1-pilot.json").read_text())
    plan = build_plan(p)
    assert len(plan) == 5472
    assert len({x["trial_id"] for x in plan}) == len(plan)
    assert plan == build_plan(p)
    assert [x["order"] for x in plan] == list(range(len(plan)))
    assert len({x["snapshot"]["now"] for x in plan[:30]}) > 1
    assert len({x["interface"] for x in plan[:30]}) == 3
    for row in plan:
        if row["snapshot"]["target_kind"] == "free" and row["interface"] != "poll":
            assert row["snapshot"]["now"] == 0
    # Every free poll is retained at every time even after earlier due snapshots.
    assert (
        sum(x["snapshot"]["target_kind"] == "free" and x["interface"] == "poll" for x in plan)
        == 720
    )
    changed = copy.deepcopy(p)
    changed["max_requests_per_participant"] = 10
    with pytest.raises(ValueError, match="budget"):
        build_plan(changed)
    changed = copy.deepcopy(p)
    changed["order_seed"] += 1
    other = build_plan(changed)
    assert [x["snapshot"] for x in plan] != [x["snapshot"] for x in other]
    assert asdict(Snapshot(**plan[0]["snapshot"])) == plan[0]["snapshot"]
