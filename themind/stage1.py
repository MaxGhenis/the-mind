"""Offline Stage 1 commands: python -m themind.stage1 --help."""

import argparse
import json
from pathlib import Path

from themind.timing import build_plan, digest, strict_json
from themind.timing_controls import CONTROLS
from themind.timing_runner import (
    finalize_run,
    import_external,
    prepare_run,
    run_control,
    verify_run,
)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Stage 1 timing snapshots — offline only, no model collection"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "control", "prepare"):
        command = sub.add_parser(name)
        command.add_argument("--protocol", type=Path, required=True)
        if name != "inspect":
            command.add_argument("--out", type=Path, required=True)
        if name == "control":
            command.add_argument("--control", choices=CONTROLS, default="oracle")
        if name == "prepare":
            command.add_argument(
                "--participant",
                type=Path,
                required=True,
                help="Exact provider/model/settings descriptor for an external collector",
            )
    command = sub.add_parser(
        "import", help="Import external attempt and result evidence into an unused prepared packet"
    )
    command.add_argument("--run", type=Path, required=True)
    command.add_argument("--attempts", type=Path, required=True)
    command.add_argument("--results", type=Path, required=True)
    command.add_argument("--allow-partial", action="store_true")
    for name in ("verify", "finalize-partial"):
        command = sub.add_parser(name)
        command.add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command in {"inspect", "control", "prepare"}:
            protocol = strict_json(args.protocol.read_text())
            if args.command == "inspect":
                plan = build_plan(protocol)
                result = {
                    "name": protocol["name"],
                    "protocol_sha256": digest(protocol),
                    "planned_requests_per_participant": len(plan),
                    "maximum_requests_per_participant": protocol["max_requests_per_participant"],
                    "model_calls": 0,
                    "collection_authorized": False,
                }
            elif args.command == "control":
                result = run_control(protocol, args.out, args.control)["counts"]
            else:
                participant = strict_json(args.participant.read_text())
                if participant["kind"] != "external":
                    raise ValueError(
                        "prepare is for external packets; use control for deterministic fixtures"
                    )
                manifest, _ = prepare_run(protocol, args.out, participant)
                result = {
                    "run_id": manifest["run_id"],
                    "planned_trials": manifest["planned_trials"],
                    "status": "prepared",
                    "collection_authorized": False,
                }
        elif args.command == "import":
            result = import_external(
                args.run, args.attempts, args.results, allow_partial=args.allow_partial
            )["counts"]
        elif args.command == "finalize-partial":
            result = finalize_run(args.run, allow_partial=True)["counts"]
        else:
            summary = verify_run(args.run)
            result = {
                "verified": True,
                "source_kind": summary["source_kind"],
                "counts": summary["counts"],
            }
        print(json.dumps(result, indent=2, allow_nan=False))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
