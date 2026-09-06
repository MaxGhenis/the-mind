"""Run `python -m themind run --suite experiments/baselines.json --out runs/demo`."""

import argparse
import asyncio
import json
from pathlib import Path

from themind.runner import run_suite, validate_suite


def main():
    parser = argparse.ArgumentParser(description="The Mind — convention compatibility experiments")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "inspect"):
        command = sub.add_parser(name)
        command.add_argument("--suite", type=Path, required=True)
        if name == "run":
            command.add_argument("--out", type=Path, required=True)
            command.add_argument("--allow-network", action="store_true")
            command.add_argument("--max-requests", type=int, default=1000)
    args = parser.parse_args()
    try:
        suite = json.loads(args.suite.read_text())
        budget = validate_suite(suite)
        if args.command == "inspect":
            print(
                json.dumps(
                    {
                        "name": suite["name"],
                        "deals": len(suite["seeds"]),
                        "conditions": len(suite["conditions"]),
                        "maximum_api_calls": budget,
                    },
                    indent=2,
                )
            )
        else:
            summary = asyncio.run(
                run_suite(
                    suite,
                    args.out,
                    allow_network=args.allow_network,
                    max_requests=args.max_requests,
                )
            )
            print(json.dumps(summary["conditions"], indent=2))
            print(f"Report: {(args.out / 'report.html').resolve()}")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
