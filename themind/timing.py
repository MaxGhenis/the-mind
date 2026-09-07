"""Stage 1: independent timing snapshots, never an advancing game or private loop.

Canonical quantities are seconds since the physical reference point. Display
coordinates may increase or decrease and have an arbitrary origin. Only the
rendered request, not the canonical scoring state, belongs in a model call.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
from dataclasses import asdict, dataclass

VERSION = "stage1-v1"
TOLERANCE = 1e-8  # canonical seconds; no rounding or clipping of responses
UNITS = {"seconds": 1, "milliseconds": 1000, "ticks": 4}
INTERFACES = ("absolute", "delay", "poll")
DIRECTIONS = ("elapsed", "countdown")
FRAMES = ("time", "magnitude")


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json(text):
    def invalid_constant(value):
        raise ValueError(f"nonfinite JSON number: {value}")

    try:
        return json.loads(text, object_pairs_hook=unique_object, parse_constant=invalid_constant)
    except (TypeError, RecursionError) as exc:
        raise ValueError("invalid JSON") from exc


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def exact_keys(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{label} must have exactly {sorted(keys)}")


@dataclass(frozen=True)
class Snapshot:
    case: str
    split: str
    now: float
    deadline: float
    target: float | None
    target_kind: str
    card: int | None = None
    step: float | None = None

    def __post_init__(self):
        if not self.case or self.split not in {"tuning", "held_out"}:
            raise ValueError("snapshot requires a case and declared split")
        if not finite(self.now) or self.now < 0 or not finite(self.deadline) or self.deadline <= 0:
            raise ValueError("invalid canonical clock")
        if self.target_kind not in {"direct", "computed", "never", "free"}:
            raise ValueError("unknown target kind")
        if self.target_kind in {"direct", "computed"}:
            if not finite(self.target) or self.target < 0:
                raise ValueError("prescribed target must be finite and nonnegative")
        elif self.target is not None:
            raise ValueError("never/free conditions have no external target")
        if self.target_kind == "computed":
            if (
                type(self.card) is not int
                or self.card < 1
                or not finite(self.step)
                or self.step <= 0
            ):
                raise ValueError("computed target needs card and positive step")
            if not math.isclose(self.card * self.step, self.target, abs_tol=TOLERANCE, rel_tol=0):
                raise ValueError("computed target differs from canonical target")
        elif self.card is not None or self.step is not None:
            raise ValueError("arithmetic inputs only belong to computed targets")
        if self.target_kind == "free" and self.now > self.deadline:
            raise ValueError("free snapshots must be within the horizon")

    @property
    def expected(self):
        if self.target_kind == "free":
            return "unscored", None
        if self.target is None or self.target > self.deadline:
            return "no_action", None
        if self.now > self.deadline:
            return "deadline_missed", None
        return "schedule", max(self.now, self.target)


@dataclass(frozen=True)
class Representation:
    unit: str = "seconds"
    direction: str = "elapsed"
    origin: float = 0
    frame: str = "time"

    def __post_init__(self):
        if self.unit not in UNITS or self.direction not in DIRECTIONS or self.frame not in FRAMES:
            raise ValueError("unknown representation")
        if not finite(self.origin):
            raise ValueError("origin must be finite")

    @property
    def scale(self):
        return UNITS[self.unit]

    @property
    def sign(self):
        return 1 if self.direction == "elapsed" else -1

    def coordinate(self, seconds, deadline):
        value = seconds if self.sign == 1 else deadline - seconds
        return (self.origin + value) * self.scale

    def seconds(self, coordinate, deadline):
        value = coordinate / self.scale - self.origin
        return value if self.sign == 1 else deadline - value


def response_schema(interface):
    if interface not in INTERFACES:
        raise ValueError("unknown interface")
    key = {"absolute": "time", "delay": "delay", "poll": "play"}[interface]
    return {
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    key: {"type": "boolean" if interface == "poll" else ["number", "null"]}
                },
                "required": [key],
                "additionalProperties": False,
            },
            {
                "type": "object",
                "properties": {"terminal": {"const": "deadline_missed"}},
                "required": ["terminal"],
                "additionalProperties": False,
            },
        ]
    }


def build_request(snapshot, representation, interface):
    """Expose one numerical representation, with no scoring answer or call history."""
    s, r = snapshot, representation
    schema = response_schema(interface)
    temporal = r.frame == "time"
    unit = (
        r.unit
        if temporal
        else {"seconds": "units", "milliseconds": "milliunits", "ticks": "steps"}[r.unit]
    )
    clock = "virtual clock" if temporal else "abstract coordinate"
    advance = "time passes" if temporal else "the coordinate progresses"
    boundary = "deadline" if temporal else "endpoint"
    system = (
        f"One optional action is evaluated on a {clock}. This is one independent snapshot, "
        "not a conversation or a continuing trajectory. No earlier choices or intervening "
        "events are supplied. Request latency has no effect. No tools or explanations. "
        f"The coordinate moves in the stated direction as {advance}, from reference to {boundary}. "
        f"All coordinates and distances use the supplied unit. The {boundary} is inclusive. "
        "For a direct target, use the supplied coordinate. For a computed target, compute "
        "reference + direction_sign * item * step_distance. For either, choose the target "
        "if it is ahead; choose current if it has already been reached but the endpoint has "
        "not passed. If the target lies beyond endpoint, choose no action. A never target "
        "requires no action at every snapshot, including endpoint and beyond. "
        "If endpoint has passed and a prescribed target was within endpoint, return exactly "
        '{"terminal":"deadline_missed"}; this records a missed opportunity, never a forced action. '
        "For a free target, select your own preferred action coordinate within the reference-to-endpoint "
        "range, or no action. There is no externally correct preference; unchanged information "
        "is supplied at each independent probe. "
    )
    system += {
        "absolute": 'Return {"time":number} for the chosen coordinate on the displayed scale, or {"time":null} for no action by endpoint. ',
        "delay": 'Return {"delay":number} for the nonnegative distance still to progress from current before acting, or {"delay":null} for no action by endpoint. ',
        "poll": 'Return {"play":true} to act at current, or {"play":false} to wait at this snapshot. A false answer does not schedule a later action. ',
    }[interface]
    system += "Return only JSON matching the supplied schema, with no fences or additional keys."
    payload = {
        "unit": unit,
        "direction_sign": r.sign,
        "reference": r.coordinate(0, s.deadline),
        "current": r.coordinate(s.now, s.deadline),
        "endpoint": r.coordinate(s.deadline, s.deadline),
        "target_kind": s.target_kind,
    }
    if r.unit == "ticks":
        payload["unit_definition"] = "1 tick = 0.25 seconds" if temporal else "1 step = 0.25 units"
    if s.target_kind == "direct":
        payload["target"] = r.coordinate(s.target, s.deadline)
    if s.target_kind == "computed":
        payload.update(item=s.card, step_distance=s.step * r.scale)
    return {
        "prompt_version": VERSION,
        "system": system,
        "user": canonical_json(payload),
        "response_schema": schema,
    }


def parse_response(text, interface, snapshot, representation):
    """Validate format without fixing numerical choices, units, signs or boundaries."""
    data = strict_json(text)
    if isinstance(data, dict) and set(data) == {"terminal"}:
        if data["terminal"] != "deadline_missed":
            raise ValueError("unknown terminal outcome")
        return {"kind": "deadline_missed", "time_seconds": None, "act_now": None}
    key = {"absolute": "time", "delay": "delay", "poll": "play"}[interface]
    exact_keys(data, {key}, "response")
    value = data[key]
    if interface == "poll":
        if type(value) is not bool:
            raise ValueError("play must be a boolean")
        return {
            "kind": "play" if value else "wait",
            "time_seconds": snapshot.now if value else None,
            "act_now": value,
        }
    if value is None:
        return {"kind": "no_action", "time_seconds": None, "act_now": False}
    if not finite(value):
        raise ValueError("time/delay must be a finite JSON number or null")
    seconds = (
        representation.seconds(value, snapshot.deadline)
        if interface == "absolute"
        else snapshot.now + value / representation.scale
    )
    if not finite(seconds):
        raise ValueError("normalized coordinate is not finite")
    return {
        "kind": "schedule",
        "time_seconds": seconds,
        "act_now": seconds <= snapshot.now + TOLERANCE,
    }


def score_response(normalized, snapshot, interface):
    """Keep target execution, binary action choice and schema validity distinct."""
    s, n = snapshot, normalized
    expectation, expected_time = s.expected
    time = n["time_seconds"]
    prescribed = s.target_kind != "free"
    terminal = expectation == "deadline_missed"
    expected_now = expectation == "schedule" and expected_time <= s.now + TOLERANCE
    error = (
        time - expected_time
        if interface != "poll" and time is not None and expected_time is not None
        else None
    )
    in_past = time is not None and time < s.now - TOLERANCE
    after_deadline = time is not None and time > s.deadline + TOLERANCE
    if terminal:
        correct = n["kind"] == "deadline_missed"
    elif expectation == "no_action":
        correct = n["kind"] in {"no_action", "wait"}
    elif interface == "poll":
        correct = n["act_now"] == expected_now and n["kind"] in {"play", "wait"}
    else:
        correct = error is not None and abs(error) <= TOLERANCE
    return {
        "external_target": prescribed,
        "expected": expectation,
        "expected_time_seconds": expected_time,
        "expected_act_now": expected_now if prescribed and not terminal else None,
        "compliant": bool(correct) if prescribed else None,
        "decision_correct": bool(n["act_now"] == expected_now)
        if prescribed and not terminal and n["act_now"] is not None
        else None,
        "target_error_seconds": error,
        "past_schedule": in_past,
        "after_deadline": after_deadline,
        "premature": bool(time is not None and s.target is not None and time < s.target - TOLERANCE)
        if prescribed
        else None,
        "late_schedule": error > TOLERANCE if error is not None else None,
        "wait_when_due": bool(expected_now and n["kind"] in {"wait", "no_action"})
        if prescribed and not terminal
        else None,
        "false_activation": bool(time is not None) if expectation == "no_action" else None,
        "correct_wait": bool(correct) if expectation == "no_action" else None,
    }


def validate_protocol(protocol):
    exact_keys(
        protocol,
        {
            "version",
            "name",
            "order_seed",
            "repetitions",
            "free_repetitions",
            "units",
            "directions",
            "origins",
            "frames",
            "cases",
            "max_requests_per_participant",
            "analysis",
        },
        "protocol",
    )
    if (
        protocol["version"] != VERSION
        or not isinstance(protocol["name"], str)
        or not protocol["name"].strip()
    ):
        raise ValueError("invalid protocol name/version")
    for field in ("repetitions", "free_repetitions", "max_requests_per_participant"):
        if type(protocol[field]) is not int or not 1 <= protocol[field] <= 100000:
            raise ValueError(f"invalid {field}")
    if type(protocol["order_seed"]) is not int:
        raise ValueError("order_seed must be an integer")
    for field, choices in (("units", UNITS), ("directions", DIRECTIONS), ("frames", FRAMES)):
        values = protocol[field]
        if (
            not isinstance(values, list)
            or not values
            or any(v not in choices for v in values)
            or len(set(values)) != len(values)
        ):
            raise ValueError(f"invalid {field}")
    origins = protocol["origins"]
    if (
        not isinstance(origins, list)
        or not origins
        or not all(finite(x) for x in origins)
        or len(set(origins)) != len(origins)
    ):
        raise ValueError("invalid origins")
    cases = protocol["cases"]
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a nonempty list")
    names = []
    for case in cases:
        exact_keys(
            case, {"id", "split", "deadline", "target", "item", "step", "kinds", "times"}, "case"
        )
        if not isinstance(case["id"], str) or not case["id"]:
            raise ValueError("case id must be nonempty")
        names.append(case["id"])
        if (
            not isinstance(case["times"], list)
            or not case["times"]
            or not all(finite(t) for t in case["times"])
            or len(set(case["times"])) != len(case["times"])
        ):
            raise ValueError("times must be unique finite numbers")
        kinds = case["kinds"]
        if not isinstance(kinds, list) or not kinds or len(set(kinds)) != len(kinds):
            raise ValueError("target kinds must be unique")
        for kind, now in itertools.product(kinds, case["times"]):
            Snapshot(
                case["id"],
                case["split"],
                now,
                case["deadline"],
                case["target"],
                kind,
                case["item"] if kind == "computed" else None,
                case["step"] if kind == "computed" else None,
            )
        if "free" in kinds and (kinds != ["free"] or 0 not in case["times"]):
            raise ValueError("free plans require a separate case including the initial snapshot")
    if len(set(names)) != len(names):
        raise ValueError("duplicate case id")
    exact_keys(
        protocol["analysis"],
        {"primary", "minimum_effect_pp", "inference", "collection_authorized"},
        "analysis",
    )
    if not isinstance(protocol["analysis"]["primary"], str) or not protocol["analysis"]["primary"]:
        raise ValueError("primary contrast required")
    if (
        not finite(protocol["analysis"]["minimum_effect_pp"])
        or not 0 < protocol["analysis"]["minimum_effect_pp"] <= 100
    ):
        raise ValueError("invalid minimum effect")
    if (
        protocol["analysis"]["inference"] != "descriptive_case_clustered"
        or protocol["analysis"]["collection_authorized"] is not False
    ):
        raise ValueError("v1 is an offline exploratory protocol; collection is not authorized")


def build_plan(protocol):
    validate_protocol(protocol)
    protocol_hash = digest(protocol)
    plan = []
    for case in protocol["cases"]:
        for kind in case["kinds"]:
            repeats = protocol["free_repetitions"] if kind == "free" else protocol["repetitions"]
            for now, rep, unit, direction, origin, frame, interface in itertools.product(
                case["times"],
                range(repeats),
                protocol["units"],
                protocol["directions"],
                protocol["origins"],
                protocol["frames"],
                INTERFACES,
            ):
                if kind == "free" and (frame == "magnitude" or (interface != "poll" and now != 0)):
                    continue
                s = Snapshot(
                    case["id"],
                    case["split"],
                    now,
                    case["deadline"],
                    case["target"],
                    kind,
                    case["item"] if kind == "computed" else None,
                    case["step"] if kind == "computed" else None,
                )
                r = Representation(unit, direction, origin, frame)
                identity = {
                    "snapshot": asdict(s),
                    "representation": asdict(r),
                    "interface": interface,
                    "repetition": rep,
                }
                request = build_request(s, r, interface)
                plan.append(
                    {
                        "trial_id": digest({"protocol_sha256": protocol_hash, **identity}),
                        **identity,
                        "request_sha256": digest(request),
                        "request": request,
                    }
                )
                if len(plan) > protocol["max_requests_per_participant"]:
                    raise ValueError("compiled plan exceeds frozen request budget")
    random.Random(protocol["order_seed"]).shuffle(plan)
    return [{"order": i, **probe} for i, probe in enumerate(plan)]
