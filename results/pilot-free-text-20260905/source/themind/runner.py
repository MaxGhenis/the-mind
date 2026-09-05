"""Paired experiment orchestration with bounded requests and auditable artifacts."""

import dataclasses
import hashlib
import json
import math
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from themind import __version__
from themind.analysis import paired_contrast, summarize
from themind.engine import Config, run_round
from themind.policies import JSONPolicy, ProportionalPolicy, RandomPolicy


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_suite(suite):
    if (
        not isinstance(suite, dict)
        or not isinstance(suite.get("name"), str)
        or not suite["name"].strip()
    ):
        raise ValueError("suite name must be a nonempty string")
    if set(suite) - {"name", "seeds", "config", "conditions", "contrasts", "notes"}:
        raise ValueError("Unknown suite fields")
    seeds = suite["seeds"]
    if not seeds or any(type(s) is not int for s in seeds) or len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be distinct integers")
    base = dict(suite.get("config", {}))
    conditions = suite["conditions"]
    if not isinstance(conditions, list) or any(
        not isinstance(c, dict) or not isinstance(c.get("name"), str) or not c["name"].strip()
        for c in conditions
    ):
        raise ValueError("condition names must be nonempty strings")
    if not conditions or len({c["name"] for c in conditions}) != len(conditions):
        raise ValueError("conditions must have distinct names")
    maximum_calls = 0
    configs = {}
    for condition in conditions:
        if set(condition) - {"name", "policies", "config"}:
            raise ValueError("Unknown condition fields")
        config = Config(**(base | condition.get("config", {})))
        configs[condition["name"]] = config
        if len(condition["policies"]) != config.players:
            raise ValueError("Each condition needs one policy specification per seat")
        network_seats = sum(p["kind"] in {"openai", "anthropic"} for p in condition["policies"])
        events = 1 if config.mode == "precommit" else config.players * config.cards_per_player
        maximum_calls += len(seeds) * network_seats * events
        for policy in condition["policies"]:
            if policy["kind"] not in {"proportional", "random", "openai", "anthropic"}:
                raise ValueError(f"Unknown policy kind: {policy['kind']}")
            forbidden = {"api_key", "token", "password", "secret"} & set(policy)
            if forbidden:
                raise ValueError("Use api_key_env names; never put credentials in experiment files")
            # Constructors perform settings validation but never load keys or call APIs.
            make_policy(policy, seed=seeds[0], seat=0, config=config)
    for name, weights in suite.get("contrasts", {}).items():
        if not set(weights) <= {c["name"] for c in conditions}:
            raise ValueError(f"Unknown condition in contrast {name}")
        if len(weights) < 2 or any(
            type(w) not in (int, float) or not math.isfinite(w) for w in weights.values()
        ):
            raise ValueError(f"Contrast {name} needs at least two finite numerical weights")
        if not math.isclose(sum(weights.values()), 0, abs_tol=1e-9) or not any(weights.values()):
            raise ValueError(f"Contrast {name} needs nonzero weights summing to zero")
        shapes = {
            (configs[c].players, configs[c].cards_per_player, configs[c].deck_size) for c in weights
        }
        if len(shapes) != 1:
            raise ValueError(f"Contrast {name} conditions must share a deal configuration")
    return maximum_calls


def make_policy(specification, *, seed, seat, config):
    spec = dict(specification)
    kind = spec.pop("kind")
    if kind == "proportional":
        return ProportionalPolicy(**spec)
    if kind == "random":
        # Independent action RNG by seat; dealing and tie RNG live in engine.
        return RandomPolicy(seed=seed * 1009 + seat * 9176 + 41, **spec)
    spec.setdefault("api_key_env", "OPENAI_API_KEY" if kind == "openai" else "ANTHROPIC_API_KEY")
    return JSONPolicy(provider=kind, mode=config.mode, **spec)


def source_snapshot(output):
    package = Path(__file__).parent
    source_dir = output / "source" / "themind"
    source_dir.mkdir(parents=True)
    hashes = {}
    for source in sorted(package.glob("*.py")):
        target = source_dir / source.name
        shutil.copyfile(source, target)
        hashes[f"themind/{source.name}"] = sha256(target)
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=package, text=True).strip()
        dirty = bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=package, text=True)
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        head, dirty = None, None
    return {"git_head": head, "git_dirty": dirty, "source_sha256": hashes}


async def run_suite(suite, output, *, allow_network=False, max_requests=1000):
    if type(max_requests) is not int or max_requests < 0:
        raise ValueError("max_requests must be a nonnegative integer")
    maximum_calls = validate_suite(suite)
    if maximum_calls and not allow_network:
        raise ValueError(
            "This suite uses model APIs; rerun with --allow-network after checking its request budget"
        )
    if maximum_calls > max_requests:
        raise ValueError(
            f"Worst-case {maximum_calls} API calls exceeds --max-requests={max_requests}"
        )
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "suite.json", suite)
    manifest = {
        "schema_version": 1,
        "package_version": __version__,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "status": "running",
        "maximum_api_calls": maximum_calls,
        "suite_sha256": sha256(output / "suite.json"),
        **source_snapshot(output),
    }
    write_json(output / "manifest.json", manifest)
    records = []
    try:
        with (output / "rounds.jsonl").open("w") as stream:
            for seed in suite["seeds"]:
                for condition in suite["conditions"]:
                    config = Config(**(suite.get("config", {}) | condition.get("config", {})))
                    policies = [
                        make_policy(p, seed=seed, seat=seat, config=config)
                        for seat, p in enumerate(condition["policies"])
                    ]
                    result = await run_round(policies, seed=seed, config=config)
                    record = {"condition": condition["name"], **dataclasses.asdict(result)}
                    records.append(record)
                    stream.write(json.dumps(record, allow_nan=False) + "\n")
                    stream.flush()
                    print(f"seed={seed} {condition['name']}: {record['status']}", flush=True)
        summary = {
            "name": suite["name"],
            "conditions": summarize(records),
            "contrasts": {
                name: paired_contrast(records, weights)
                for name, weights in suite.get("contrasts", {}).items()
            },
        }
        write_json(output / "summary.json", summary)
        from themind.report import render_report

        (output / "report.html").write_text(render_report(summary, records, suite))
        manifest.update(status="complete", completed_at=datetime.now(timezone.utc).isoformat())
        manifest["artifact_sha256"] = {
            name: sha256(output / name) for name in ("rounds.jsonl", "summary.json", "report.html")
        }
        write_json(output / "manifest.json", manifest)
        return summary
    except BaseException as exc:
        manifest.update(
            status="aborted", error_type=type(exc).__name__, completed_rounds=len(records)
        )
        write_json(output / "manifest.json", manifest)
        raise
