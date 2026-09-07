"""Reproduce and verify the frozen pilot's deterministic control signatures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from themind.runner import sha256
from themind.timing import build_plan, digest, exact_keys, strict_json
from themind.timing_runner import run_control, verify_run, write_json

VALIDATION_CONTROLS = (
    "oracle",
    "unit_blind",
    "origin_blind",
    "arithmetic_blind",
    "poll_early",
    "always_wait",
    "always_play",
)


def check_signatures(summaries):
    """Fail loudly if the instrument cannot distinguish a known software fault."""
    checks = {}
    for name, summary in summaries.items():
        checks[f"{name}:complete_valid_coverage"] = (
            summary["counts"]["planned"] == summary["counts"]["valid"]
        )
    oracle = summaries["oracle"]
    checks["oracle:prescribed_compliance"] = oracle["instrument_checks"][
        "all_prescribed_snapshots_compliant"
    ]
    checks["oracle:representation_agreement"] = bool(oracle["representation_agreement"]) and all(
        x["agreement"] == 1 for x in oracle["representation_agreement"]
    )
    checks["oracle:free_q_equals_F"] = bool(oracle["free_policy_curves"]) and all(
        x["q_minus_F_absolute"] == x["q_minus_F_delay"] == 0
        for c in oracle["free_policy_curves"]
        for x in c["points"]
    )

    def strata(name, **where):
        return [
            s
            for s in summaries[name]["strata"]
            if s["target_kind"] != "free" and all(s[k] == v for k, v in where.items())
        ]

    def all_pass(cells):
        return bool(cells) and all(s["valid_only_compliance"] == 1 for s in cells)

    checks["unit_blind:correct_polls"] = all_pass(strata("unit_blind", interface="poll"))
    checks["unit_blind:numerical_errors"] = (
        summaries["unit_blind"]["counts"]["mean_absolute_target_error_seconds"] > 0
    )
    checks["origin_blind:correct_delays_and_polls"] = all_pass(
        strata("origin_blind", interface="delay") + strata("origin_blind", interface="poll")
    )
    checks["origin_blind:absolute_errors"] = any(
        s["valid_only_compliance"] < 1 for s in strata("origin_blind", interface="absolute")
    )
    checks["arithmetic_blind:direct_passes"] = all_pass(
        strata("arithmetic_blind", target_kind="direct")
    )
    checks["arithmetic_blind:computed_fails"] = any(
        s["valid_only_compliance"] < 1 for s in strata("arithmetic_blind", target_kind="computed")
    )
    checks["poll_early:numerical_plans_pass"] = all_pass(
        strata("poll_early", interface="absolute") + strata("poll_early", interface="delay")
    )
    checks["poll_early:magnitude_polls_pass"] = all_pass(
        strata("poll_early", interface="poll", frame="magnitude")
    )
    checks["poll_early:time_polls_fail"] = any(
        s["valid_only_compliance"] < 1 for s in strata("poll_early", interface="poll", frame="time")
    )
    for name in ("always_wait", "always_play"):
        never = summaries[name]["never_snapshot_sets"]
        field = (
            "correct_wait_at_every_snapshot_including_deadline"
            if name == "always_wait"
            else "sets_with_false_activation"
        )
        checks[f"{name}:never_due_signature"] = (
            never["planned_snapshot_sets"] > 0 and never[field] == never["planned_snapshot_sets"]
        )
    checks["always_wait:due_omissions"] = summaries["always_wait"]["counts"]["wait_when_due"] > 0
    failures = [name for name, passed in checks.items() if not passed]
    if failures:
        raise ValueError("control validation failed: " + ", ".join(failures))
    return checks


def validation_report(summaries, checks):
    first = summaries["oracle"]
    lines = [
        "# Stage 1 offline control validation",
        "",
        "**These are deterministic software controls, not model results. No model collection occurred.**",
        f"Protocol: `{first['protocol_sha256']}`. {len(checks)} control-signature checks passed.",
        "",
        "Each control has a complete frozen request grid, separate original attempt/result ledgers, source snapshot and independently recomputable report. The verifier also replays every deterministic response from its rendered request.",
        "",
        "| Control | Valid / planned | Compliant / prescribed | Mean absolute numeric error (seconds) | Binary decision accuracy |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name in VALIDATION_CONTROLS:
        c = summaries[name]["counts"]
        error = c["mean_absolute_target_error_seconds"]
        binary = c["binary_decision_accuracy"]
        lines.append(
            f"| [{name}]({name}/report.md) | {c['valid']}/{c['planned']} | {c['compliant']}/{c['external_target_valid']} | {'—' if error is None else f'{error:.6g}'} | {'—' if binary is None else f'{100 * binary:.2f}%'} |"
        )
    lines.extend(
        [
            "",
            "The oracle passes all prescribed snapshots. Unit and origin faults change numeric plans while leaving polls correct. The early-poll control changes time-framed binary decisions while its numeric plans and magnitude-framed polls remain correct. Arithmetic faults are separated by direct/computed conditions. Constant WAIT and PLAY distinguish never-due waiting from omitted or premature due actions.",
            "",
            "Numeric means use only numeric answers with a reference. Null and incorrect terminal choices remain in prescribed compliance; they are not silently imputed into the error mean. Binary accuracy is a different diagnostic and is not evidence that a numeric schedule is correct.",
            "",
            "The full reports keep planned/attempted/valid denominators, case-level framing/arithmetic/interface contrasts, transformation-specific agreement and free-policy F/q curves. q is an independent snapshot probability, not a trajectory hazard. Test-suite fixtures separately exercise malformed JSON, refusals, truncation, provider errors and interrupted or altered evidence.",
            "",
            "This validates the offline instrument, not any model capability, temporal mechanism, partner coordination claim or statistical power. Hosted collection and independent review require their own completed gates.",
            "",
        ]
    )
    return "\n".join(lines)


def run_validation(protocol, output):
    output = Path(output)
    plan = build_plan(protocol)  # validate budget before creating any artifact
    output.mkdir(parents=True, exist_ok=False)
    summaries = {}
    for control in VALIDATION_CONTROLS:
        summary = run_control(protocol, output / control, control)
        if verify_run(output / control) != summary:
            raise ValueError(f"verification differs: {control}")
        summaries[control] = summary
        print(f"Verified {control}: {summary['counts']['valid']}/{len(plan)} valid", flush=True)
    checks = check_signatures(summaries)
    manifests = {
        name: strict_json((output / name / "manifest.json").read_text())
        for name in VALIDATION_CONTROLS
    }
    source = manifests["oracle"]["source_sha256"]
    if any(m["source_sha256"] != source for m in manifests.values()):
        raise ValueError("control source changed during validation")
    index = {
        "schema_version": 1,
        "source_kind": "deterministic_offline_controls",
        "protocol_sha256": digest(protocol),
        "source_sha256": source,
        "requests_per_control": len(plan),
        "total_control_responses": sum(s["counts"]["valid"] for s in summaries.values()),
        "model_calls": 0,
        "checks": checks,
        "manifest_sha256": {
            name: sha256(output / name / "manifest.json") for name in VALIDATION_CONTROLS
        },
    }
    (output / "report.md").write_text(validation_report(summaries, checks))
    index["report_sha256"] = sha256(output / "report.md")
    write_json(output / "validation.json", index)
    return index


def verify_validation(output):
    output = Path(output)
    index = strict_json((output / "validation.json").read_text())
    exact_keys(
        index,
        {
            "schema_version",
            "source_kind",
            "protocol_sha256",
            "source_sha256",
            "requests_per_control",
            "total_control_responses",
            "model_calls",
            "checks",
            "manifest_sha256",
            "report_sha256",
        },
        "validation index",
    )
    if set(index["manifest_sha256"]) != set(VALIDATION_CONTROLS):
        raise ValueError("incomplete control inventory")
    summaries = {}
    for name in VALIDATION_CONTROLS:
        if sha256(output / name / "manifest.json") != index["manifest_sha256"][name]:
            raise ValueError(f"control manifest hash mismatch: {name}")
        manifest = strict_json((output / name / "manifest.json").read_text())
        if manifest["source_sha256"] != index["source_sha256"]:
            raise ValueError("control source differs across the validation")
        summaries[name] = verify_run(output / name)
    if any(s["protocol_sha256"] != index["protocol_sha256"] for s in summaries.values()):
        raise ValueError("controls use different protocols")
    if (
        index["schema_version"] != 1
        or index["model_calls"] != 0
        or index["source_kind"] != "deterministic_offline_controls"
    ):
        raise ValueError("invalid validation provenance")
    if any(
        s["participant"]["kind"] != "deterministic_control" or s["participant"]["name"] != name
        for name, s in summaries.items()
    ):
        raise ValueError("invalid validation control identity")
    if (
        any(s["counts"]["planned"] != index["requests_per_control"] for s in summaries.values())
        or sum(s["counts"]["valid"] for s in summaries.values()) != index["total_control_responses"]
    ):
        raise ValueError("validation counts differ from response evidence")
    checks = check_signatures(summaries)
    if (
        checks != index["checks"]
        or validation_report(summaries, checks) != (output / "report.md").read_text()
        or sha256(output / "report.md") != index["report_sha256"]
    ):
        raise ValueError("validation report/checks differ from evidence")
    return index


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Reproduce the seven offline Stage 1 controls; no model calls"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--protocol", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = (
            run_validation(strict_json(args.protocol.read_text()), args.out)
            if args.command == "run"
            else verify_validation(args.run)
        )
        print(json.dumps(result, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
