"""Deterministic positive and fault controls; none are model observations.

The oracle reads only the rendered request. It does not call the scoring oracle
or use canonical target values. Deliberate faults make report dimensions testable.
"""

import json

from themind.timing import VERSION, canonical_json

CONTROLS = (
    "oracle",
    "always_wait",
    "always_play",
    "unit_blind",
    "origin_blind",
    "arithmetic_blind",
    "invalid_json",
    "refusal",
    "truncated",
    "provider_error",
)


def descriptor(name):
    if name not in CONTROLS:
        raise ValueError(f"unknown control: {name}")
    return {
        "kind": "deterministic_control",
        "name": name,
        "provider": "offline",
        "model_requested": f"control/{name}@{VERSION}",
        "settings": {"version": VERSION},
    }


def control_response(name, request, repetition=0):
    """Synthetic response metadata is explicitly marked offline, never a provider ID."""
    descriptor(name)
    p = json.loads(request["user"])
    key = request["response_schema"]["oneOf"][0]["required"][0]
    sign = p["direction_sign"]
    current = sign * (p["current"] - p["reference"])
    horizon = sign * (p["endpoint"] - p["reference"])
    kind = p["target_kind"]
    if kind == "direct":
        target = sign * (p["target"] - p["reference"])
    elif kind == "computed":
        target = p["item"] * p["step_distance"]
        if name == "arithmetic_blind":
            target = p["item"]  # omit the supplied step size
    elif kind == "free":
        # A retained, counterbalanced threshold distribution: F = {1/4,1/2,3/4}.
        # Repetition is private test-control randomness, never a model prompt cue.
        target = horizon * (1 + repetition % 3) / 4
    else:
        target = None
    if target is not None and target <= horizon and current > horizon:
        answer = {"terminal": "deadline_missed"}
    elif key == "play":
        answer = {key: target is not None and target <= horizon and current >= target}
    elif target is None or target > horizon:
        answer = {key: None}
    else:
        selected = max(current, target)
        answer = {key: p["reference"] + sign * selected if key == "time" else selected - current}
    if name == "always_wait":
        answer = {key: False if key == "play" else None}
    if name == "always_play":
        answer = {key: True if key == "play" else p["current"] if key == "time" else 0}
    if name == "unit_blind" and key in answer and answer[key] is not None and key != "play":
        # Emit the correct seconds-scale number even when another unit is requested.
        scale = {
            "seconds": 1,
            "milliseconds": 1000,
            "ticks": 4,
            "units": 1,
            "milliunits": 1000,
            "steps": 4,
        }[p["unit"]]
        answer[key] /= scale
    if name == "origin_blind" and key == "time" and key in answer and answer[key] is not None:
        anchor = p["reference"] if sign == 1 else p["endpoint"]
        answer[key] -= anchor
    status, finish, error = "success", "stop", None
    text = canonical_json(answer)
    if name == "invalid_json":
        text = '{"play":"yes"}' if key == "play" else '{"' + key + '":true}'
    if name == "refusal":
        status, finish, text = "refusal", "refusal", "OFFLINE FIXTURE: refusal"
    if name == "truncated":
        # Deliberately valid-looking prefix: finish metadata must override parseability.
        status, finish = "truncated", "length"
    if name == "provider_error":
        status, finish, text, error = (
            "provider_error",
            "error",
            None,
            "OFFLINE FIXTURE: transport error",
        )
    return {
        "status": status,
        "raw_text": text,
        "raw_response": canonical_json(
            {"synthetic": True, "control": name, "text": text, "error": error}
        ),
        "model_returned": f"control/{name}@{VERSION}",
        "provider_request_id": None,
        "finish_reason": finish,
        "input_tokens": 0,
        "output_tokens": 0,
        "error": error,
    }
