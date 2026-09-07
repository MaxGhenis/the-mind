"""Descriptive Stage 1 analysis; snapshot probabilities are not trajectory hazards."""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict

from themind.timing import TOLERANCE


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def mean(values):
    return statistics.mean(values) if values else None


def cell_stats(rows):
    valid = [r for r in rows if r["status"] == "valid"]
    scored = [r for r in valid if r["score"]["external_target"]]
    attempted = [r for r in rows if r["status"] != "not_attempted"]
    attempted_scored = [r for r in attempted if r["snapshot"]["target_kind"] != "free"]
    errors = [
        r["score"]["target_error_seconds"]
        for r in valid
        if r["score"]["target_error_seconds"] is not None
    ]
    decisions = [
        r["score"]["decision_correct"] for r in valid if r["score"]["decision_correct"] is not None
    ]
    n_correct = sum(r["score"]["compliant"] is True for r in scored)
    return {
        "planned": len(rows),
        "attempted": len(attempted),
        "valid": len(valid),
        "statuses": dict(sorted(Counter(r["status"] for r in rows).items())),
        "external_target_valid": len(scored),
        "external_target_attempted": len(attempted_scored),
        "compliant": n_correct,
        "all_attempt_observed_compliance": ratio(n_correct, len(attempted_scored)),
        "valid_only_compliance": ratio(n_correct, len(scored)),
        "numeric_responses_with_reference": len(errors),
        "mean_absolute_target_error_seconds": mean([abs(x) for x in errors]),
        "mean_signed_target_error_seconds": mean(errors),
        "exact_numeric_responses": sum(abs(x) <= TOLERANCE for x in errors),
        "binary_decisions_with_reference": len(decisions),
        "binary_decision_accuracy": mean(decisions),
        **{
            key: sum(r["score"][key] is True for r in valid)
            for key in (
                "premature",
                "late_schedule",
                "past_schedule",
                "after_deadline",
                "wait_when_due",
                "false_activation",
                "correct_wait",
            )
        },
    }


def group_by(rows, key):
    groups = defaultdict(list)
    for row in rows:
        groups[key(row)].append(row)
    return groups


def pair_key(row, *, omit=()):
    s, r = row["snapshot"], row["representation"]
    fields = {
        "case": s["case"],
        "split": s["split"],
        "now": s["now"],
        "target_kind": s["target_kind"],
        "repetition": row["repetition"],
        "interface": row["interface"],
        **r,
    }
    return tuple((k, v) for k, v in fields.items() if k not in omit)


def paired_effect(pairs, field="compliant"):
    """Equal-weight case means; repeated snapshots are never independent samples."""
    all_case, valid_case = defaultdict(list), defaultdict(list)
    both_attempted = both_valid = eligible = 0
    for a, b in pairs:
        if a is None or b is None:
            continue
        if a["status"] != "not_attempted" and b["status"] != "not_attempted":
            both_attempted += 1
            if field == "compliant":
                # Observed compliance, not inferred failure when evidence is unavailable.
                observed_a = a["status"] == "valid" and a["score"][field] is True
                observed_b = b["status"] == "valid" and b["score"][field] is True
                all_case[a["snapshot"]["case"]].append(int(observed_a) - int(observed_b))
        if a["status"] == b["status"] == "valid":
            both_valid += 1
            x, y = a["score"][field], b["score"][field]
            if x is not None and y is not None:
                eligible += 1
                valid_case[a["snapshot"]["case"]].append(int(x) - int(y))
    return {
        "planned_pairs": len(pairs),
        "both_attempted": both_attempted,
        "both_valid": both_valid,
        "both_eligible_for_metric": eligible,
        "independent_case_count": len(valid_case),
        "all_attempt_case_mean_difference": mean([mean(v) for v in all_case.values()]),
        "valid_only_case_mean_difference": mean([mean(v) for v in valid_case.values()]),
        "case_differences": {k: mean(v) for k, v in sorted(valid_case.items())},
    }


def paired_contrasts(rows):
    output = []
    specifications = [
        ("time_minus_magnitude", "frame", "time", "magnitude", "compliant"),
        ("computed_minus_direct", "target_kind", "computed", "direct", "compliant"),
        ("delay_minus_absolute", "interface", "delay", "absolute", "decision_correct"),
        ("poll_minus_absolute", "interface", "poll", "absolute", "decision_correct"),
    ]
    for name, axis, left, right, metric in specifications:
        groups = defaultdict(dict)
        for row in rows:
            if row["snapshot"]["target_kind"] == "free":
                continue
            value = (
                row["interface"]
                if axis == "interface"
                else row["snapshot"].get(axis, row["representation"].get(axis))
            )
            if value in {left, right}:
                groups[pair_key(row, omit=(axis,))][value] = row
        strata = defaultdict(list)
        for choices in groups.values():
            if left not in choices or right not in choices:
                continue  # structurally unpaired cases are not a designed contrast
            row = choices[left]
            strata[
                (
                    row["snapshot"]["split"],
                    "paired" if axis == "target_kind" else row["snapshot"]["target_kind"],
                    "paired" if axis == "interface" else row["interface"],
                    "paired" if axis == "frame" else row["representation"]["frame"],
                )
            ].append((choices[left], choices[right]))
        for (split, kind, interface, frame), pairs in sorted(strata.items()):
            output.append(
                {
                    "contrast": name,
                    "metric": metric,
                    "split": split,
                    "target_kind": kind,
                    "interface": interface,
                    "frame": frame,
                    **paired_effect(pairs, metric),
                }
            )
    return output


def equivalent(a, b):
    x, y = a["normalized"], b["normalized"]
    if x["kind"] != y["kind"]:
        return False
    if x["time_seconds"] is None or y["time_seconds"] is None:
        return x["time_seconds"] == y["time_seconds"] and x["act_now"] == y["act_now"]
    return abs(x["time_seconds"] - y["time_seconds"]) <= TOLERANCE


def representation_agreement(rows):
    # Free responses are stochastic independent choices in real data, so equality
    # of individual free samples is NOT treated as an invariance/compliance test.
    groups = group_by(
        [r for r in rows if r["snapshot"]["target_kind"] != "free"],
        lambda r: pair_key(r, omit=("unit", "direction", "origin")),
    )
    comparisons = defaultdict(list)
    for group in groups.values():
        baseline = next(
            (
                r
                for r in group
                if (
                    r["representation"]["unit"],
                    r["representation"]["direction"],
                    r["representation"]["origin"],
                )
                == ("seconds", "elapsed", 0)
            ),
            None,
        )
        if baseline is None:
            continue
        for row in group:
            if row is baseline:
                continue
            r = row["representation"]
            comparisons[
                (r["unit"], r["direction"], r["origin"], row["interface"], r["frame"])
            ].append((row, baseline))
    output = []
    for (unit, direction, origin, interface, frame), pairs in sorted(comparisons.items()):
        valid = [(a, b) for a, b in pairs if a["status"] == b["status"] == "valid"]
        agreements = sum(equivalent(a, b) for a, b in valid)
        output.append(
            {
                "unit": unit,
                "direction": direction,
                "origin": origin,
                "interface": interface,
                "frame": frame,
                "planned_pairs": len(pairs),
                "both_valid": len(valid),
                "equivalent": agreements,
                "agreement": ratio(agreements, len(valid)),
                "case_count": len({a["snapshot"]["case"] for a, b in valid}),
            }
        )
    return output


def free_policy_curves(rows):
    groups = group_by(
        [r for r in rows if r["snapshot"]["target_kind"] == "free"],
        lambda r: (
            r["snapshot"]["case"],
            r["representation"]["unit"],
            r["representation"]["direction"],
            r["representation"]["origin"],
        ),
    )
    curves = []
    for (case, unit, direction, origin), group in sorted(groups.items()):
        times = sorted({r["snapshot"]["now"] for r in group if r["interface"] == "poll"})
        plans = {
            interface: [r for r in group if r["interface"] == interface]
            for interface in ("absolute", "delay")
        }
        valid_plans = {
            interface: [
                r
                for r in selected
                if r["status"] == "valid" and r["normalized"]["kind"] in {"schedule", "no_action"}
            ]
            for interface, selected in plans.items()
        }
        points = []
        for now in times:
            polls = [r for r in group if r["interface"] == "poll" and r["snapshot"]["now"] == now]
            valid_polls = [
                r
                for r in polls
                if r["status"] == "valid" and r["normalized"]["kind"] in {"play", "wait"}
            ]
            q = ratio(sum(r["normalized"]["act_now"] for r in valid_polls), len(valid_polls))
            point = {
                "time_seconds": now,
                "poll_planned": len(polls),
                "poll_valid_decisions": len(valid_polls),
                "q": q,
            }
            for interface, selected in valid_plans.items():
                F = ratio(
                    sum(
                        r["normalized"]["time_seconds"] is not None
                        and r["normalized"]["time_seconds"] <= now + TOLERANCE
                        for r in selected
                    ),
                    len(selected),
                )
                point[f"F_{interface}"] = F
                point[f"q_minus_F_{interface}"] = q - F if q is not None and F is not None else None
            points.append(point)
        decreases = sum(
            b["q"] < a["q"]
            for a, b in zip(points, points[1:])
            if a["q"] is not None and b["q"] is not None
        )
        curves.append(
            {
                "case": case,
                "unit": unit,
                "direction": direction,
                "origin": origin,
                "plans": {
                    interface: {
                        "planned": len(plans[interface]),
                        "valid_schedule_or_no_action": len(selected),
                        "no_action": sum(r["normalized"]["kind"] == "no_action" for r in selected),
                        "past_reference": sum(r["score"]["past_schedule"] for r in selected),
                        "after_deadline": sum(r["score"]["after_deadline"] for r in selected),
                    }
                    for interface, selected in valid_plans.items()
                },
                "q_adjacent_decreases": decreases,
                "points": points,
            }
        )
    return curves


def never_snapshot_sets(rows):
    groups = group_by(
        [
            r
            for r in rows
            if r["snapshot"]["target_kind"] == "never"
            and r["snapshot"]["now"] <= r["snapshot"]["deadline"]
        ],
        lambda r: pair_key(r, omit=("now",)),
    )
    valid_sets = all_wait = false_activation_sets = 0
    for group in groups.values():
        if all(r["status"] == "valid" for r in group):
            valid_sets += 1
            all_wait += all(r["score"]["correct_wait"] for r in group)
        false_activation_sets += any(
            r["status"] == "valid" and r["score"]["false_activation"] for r in group
        )
    return {
        "planned_snapshot_sets": len(groups),
        "all_snapshots_valid": valid_sets,
        "correct_wait_at_every_snapshot_including_deadline": all_wait,
        "sets_with_false_activation": false_activation_sets,
        "interpretation": "Independent snapshot sets, not observed trajectories or survival probabilities.",
    }


def summarize(rows, protocol, manifest):
    if len({r["trial_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate trial in analysis")
    groups = group_by(
        rows,
        lambda r: (
            r["snapshot"]["split"],
            r["snapshot"]["target_kind"],
            r["representation"]["frame"],
            r["interface"],
        ),
    )
    strata = [
        {
            "split": split,
            "target_kind": kind,
            "frame": frame,
            "interface": interface,
            **cell_stats(group),
        }
        for (split, kind, frame, interface), group in sorted(groups.items())
    ]
    counts = cell_stats(rows)
    failures = counts["planned"] - counts["valid"]
    prescribed = [r for r in rows if r["snapshot"]["target_kind"] != "free"]
    compliance_pass = bool(prescribed) and all(
        r["status"] == "valid" and r["score"]["compliant"] for r in prescribed
    )
    return {
        "analysis_version": "stage1-v1",
        "name": protocol["name"],
        "protocol_sha256": manifest["protocol_sha256"],
        "participant": manifest["participant"],
        "source_kind": manifest["source_kind"],
        "counts": counts,
        "resource_usage": {
            "input_tokens_known_total": sum(
                r["input_tokens"] for r in rows if r["input_tokens"] is not None
            ),
            "output_tokens_known_total": sum(
                r["output_tokens"] for r in rows if r["output_tokens"] is not None
            ),
            "responses_with_input_tokens": sum(r["input_tokens"] is not None for r in rows),
            "responses_with_output_tokens": sum(r["output_tokens"] is not None for r in rows),
            "responses_with_latency": sum(r["latency_seconds"] is not None for r in rows),
            "latency_seconds_mean": mean(
                [r["latency_seconds"] for r in rows if r["latency_seconds"] is not None]
            ),
        },
        "returned_models": dict(
            sorted(
                Counter(
                    r["model_returned"] for r in rows if r["model_returned"] is not None
                ).items()
            )
        ),
        "instrument_checks": {
            "all_planned_responses_valid": failures == 0,
            "all_prescribed_snapshots_compliant": compliance_pass,
            "coordination_claims_authorized": False,
        },
        "strata": strata,
        "paired_contrasts": paired_contrasts(rows),
        "representation_agreement": representation_agreement(rows),
        "never_snapshot_sets": never_snapshot_sets(rows),
        "free_policy_curves": free_policy_curves(rows),
        "limits": [
            "Deterministic controls are software checks, not model performance or empirical research results."
            if manifest["participant"]["kind"] == "deterministic_control"
            else "Imported collector evidence is hash-linked but not provider-authenticated; no model calls were made by this harness.",
            "All-attempt observed compliance treats unavailable evidence as no observed compliance, not behavioral failure. Valid-only rates may be selected.",
            "Numerical error uses only numeric absolute/delay responses with an external reference; omissions and terminal choices remain visible in overall compliance.",
            "Contrasts average paired differences within case, then equally across cases. Repeated snapshots are not independent trials; no inferential intervals or power claims are made.",
            "Free q(t) is an uncensored independent snapshot probability. F(t) is the initial schedule CDF. Their equality is a latent-threshold hypothesis, not a requirement of every stable policy.",
            "Free CDF denominators include every schema-valid schedule/null, including beyond-deadline mass; null and future mass are not renormalized away. Out-of-range schedules are reported separately.",
            "Free-sample pairwise equality is not scored. q monotonicity counts and q-F gaps are descriptive, not individual contradictions or trajectory hazards.",
            "This exploratory protocol uses a fixed, small case library. Held_out is a predeclared case split, not evidence of population generalization or an adequately powered confirmatory study.",
        ],
    }


def percent(value):
    return "—" if value is None else f"{100 * value:.1f}%"


def safe(text):
    return (
        str(text).replace("|", "\\|").replace("\n", " ").replace("<", "&lt;").replace(">", "&gt;")
    )


def render_report(summary):
    c, p = summary["counts"], summary["participant"]
    lines = [
        f"# {safe(summary['name'])}",
        "",
        f"Participant: **{safe(p['name'])}** · source: `{summary['source_kind']}`.",
        f"Frozen protocol: `{summary['protocol_sha256']}`.",
        "",
        f"{c['planned']} planned snapshots; {c['attempted']} attempts; {c['valid']} valid responses. "
        f"External-target compliance: {c['compliant']}/{c['external_target_attempted']} observed across attempts "
        f"({percent(c['all_attempt_observed_compliance'])}); {c['compliant']}/{c['external_target_valid']} among valid responses "
        f"({percent(c['valid_only_compliance'])}). Free preferences have no correct target.",
        "",
        "## Attempt and result outcomes",
        "",
        "| Outcome | Count |",
        "| --- | ---: |",
        *[f"| {safe(k)} | {v} |" for k, v in c["statuses"].items()],
        "",
        "## Numerical execution and action decisions",
        "",
        "Exact-target compliance requires the correct timestamp/delay or PLAY/WAIT/terminal choice. "
        "Binary accuracy asks only whether to act now. A wrong future timestamp can pass that binary "
        "check while failing numerical execution. Do not filter out failed numerical trials to claim a timing effect.",
        "",
        "| Split / target / frame / interface | Valid / planned | Compliant / externally scored | Mean absolute error (seconds) | Binary accuracy (n) |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for s in summary["strata"]:
        label = " / ".join(s[k] for k in ("split", "target_kind", "frame", "interface"))
        error = s["mean_absolute_target_error_seconds"]
        lines.append(
            f"| {label} | {s['valid']}/{s['planned']} | {s['compliant']}/{s['external_target_valid']} | {'—' if error is None else f'{error:.6g}'} | {percent(s['binary_decision_accuracy'])} ({s['binary_decisions_with_reference']}) |"
        )
    lines.extend(
        [
            "",
            "## Primary paired framing contrast",
            "",
            "Time minus magnitude; equal-weight case means. Full arithmetic/interface contrasts and individual case means are in `summary.json`.",
            "",
            "| Split / target / interface | Both valid / planned pairs | Cases | All-attempt observed difference | Valid-only difference |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for s in summary["paired_contrasts"]:
        if s["contrast"] == "time_minus_magnitude":
            lines.append(
                f"| {s['split']} / {s['target_kind']} / {s['interface']} | {s['both_valid']}/{s['planned_pairs']} | {s['independent_case_count']} | {percent(s['all_attempt_case_mean_difference'])} | {percent(s['valid_only_case_mean_difference'])} |"
            )
    reps = summary["representation_agreement"]
    lines.extend(
        [
            "",
            "## Representation and never-due controls",
            "",
            f"Equivalent normalized answers in {sum(s['equivalent'] for s in reps)}/{sum(s['both_valid'] for s in reps)} valid representation pairs; {sum(s['planned_pairs'] for s in reps)} planned pairs. These are prescribed targets only. Transformation-specific denominators are retained in `summary.json`.",
        ]
    )
    n = summary["never_snapshot_sets"]
    lines.extend(
        [
            "",
            f"Never-due: correct waiting at every scheduled snapshot through the inclusive deadline in {n['correct_wait_at_every_snapshot_including_deadline']}/{n['planned_snapshot_sets']} sets; {n['all_snapshots_valid']} sets have complete valid evidence; {n['sets_with_false_activation']} have a false activation. {n['interpretation']}",
            "",
            "## Free timing decisions",
            "",
            "F uses plans requested only at the fixed initial origin; q uses independent polls at every probe time, even after earlier PLAY answers. No virtual trajectory is simulated. All representation-specific curves are in `summary.json`.",
        ]
    )
    baseline = next(
        (
            x
            for x in summary["free_policy_curves"]
            if (x["unit"], x["direction"], x["origin"]) == ("seconds", "elapsed", 0)
        ),
        None,
    )
    if baseline:
        lines.extend(
            [
                "",
                "Baseline seconds / elapsed / origin 0:",
                "",
                "| Time | F absolute | F delay | q PLAY | Valid polls / planned |",
                "| ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for x in baseline["points"]:
            lines.append(
                f"| {x['time_seconds']} | {percent(x['F_absolute'])} | {percent(x['F_delay'])} | {percent(x['q'])} | {x['poll_valid_decisions']}/{x['poll_planned']} |"
            )
    lines.extend(["", "## Interpretation limits", "", *[f"- {x}" for x in summary["limits"]], ""])
    return "\n".join(lines)
