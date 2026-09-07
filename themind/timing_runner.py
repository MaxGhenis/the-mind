"""Offline collection packets and append-only, hash-linked attempt/result ledgers.

No network client or provider credentials are loaded here. An external adapter
can produce the documented two ledgers for later import, after collection is
separately authorized. Exported requests never include private scoring state.
"""

from __future__ import annotations

import gzip
import json
import os
import platform
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from themind.runner import sha256, source_snapshot
from themind.timing import (
    VERSION,
    Representation,
    Snapshot,
    build_plan,
    canonical_json,
    digest,
    exact_keys,
    finite,
    parse_response,
    score_response,
    strict_json,
)
from themind.timing_controls import control_response, descriptor

ZERO_HASH = "0" * 64
MANIFEST_VERSION = 1
STATUSES = {"success", "refusal", "truncated", "provider_error"}
ATTEMPT_KEYS = {
    "attempt_id",
    "run_id",
    "trial_id",
    "request_sha256",
    "participant_sha256",
    "started_at",
}
RESULT_KEYS = {
    "attempt_id",
    "run_id",
    "trial_id",
    "request_sha256",
    "participant_sha256",
    "completed_at",
    "latency_seconds",
    "status",
    "raw_text",
    "raw_response",
    "model_returned",
    "provider_request_id",
    "finish_reason",
    "input_tokens",
    "output_tokens",
    "error",
}


def write_json(path, value):
    """Replace a manifest atomically; interruption leaves the previous checkpoint."""
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def timestamp(text):
    if not isinstance(text, str):
        raise ValueError("timestamp must be an ISO string with timezone")
    try:
        value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid ISO timestamp") from exc
    if value.utcoffset() is None:
        raise ValueError("timestamp must include timezone")
    return value


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def validate_participant(p):
    exact_keys(p, {"kind", "name", "provider", "model_requested", "settings"}, "participant")
    if (
        p["kind"] not in {"deterministic_control", "external"}
        or not all(nonempty(p[k]) for k in ("name", "provider", "model_requested"))
        or not isinstance(p["settings"], dict)
    ):
        raise ValueError("invalid participant descriptor")

    # Configuration must never carry credential values, including nested settings.
    def reject_secrets(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key.lower() in {
                    "api_key",
                    "token",
                    "password",
                    "secret",
                    "authorization",
                    "credentials",
                }:
                    raise ValueError("participant settings must not contain credentials")
                reject_secrets(child)
        elif isinstance(value, list):
            for child in value:
                reject_secrets(child)

    reject_secrets(p)
    canonical_json(p)
    if p["kind"] == "deterministic_control" and p != descriptor(p["name"]):
        raise ValueError("control identity/settings do not match implementation")
    if p["kind"] == "external" and p["provider"] == "offline":
        raise ValueError("external responses cannot impersonate offline controls")


def write_jsonl_gz(path, rows):
    with path.open("xb") as stream:
        _write_jsonl_gz_stream(stream, rows)


def _write_jsonl_gz_stream(stream, rows):
    # Fixed mtime and no filename make identical packets byte reproducible.
    with gzip.GzipFile(filename="", fileobj=stream, mode="wb", mtime=0) as zipped:
        for row in rows:
            zipped.write((canonical_json(row) + "\n").encode())


@contextmanager
def _atomic_derived_file(path):
    """Replace a derived file only after its complete contents are durable.

    Used only after finalize_run's unsealed-run guard and evidence validation.
    A unique sibling temporary also permits retries after a hard interruption
    leaves an old temporary behind. Raw packets and journals never use this path.
    """
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_jsonl(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                raise ValueError("blank ledger/packet line")
            yield strict_json(line)


def chain_rows(records):
    previous = ZERO_HASH
    for seq, record in enumerate(records):
        body = {"seq": seq, "previous_sha256": previous, "record": record}
        row = {**body, "sha256": digest(body)}
        previous = row["sha256"]
        yield row


def read_chain(path):
    previous = ZERO_HASH
    records = []
    for seq, row in enumerate(read_jsonl(path)):
        exact_keys(row, {"seq", "previous_sha256", "record", "sha256"}, "ledger row")
        if type(row["seq"]) is not int or row["seq"] != seq or row["previous_sha256"] != previous:
            raise ValueError("broken ledger order/hash chain")
        body = {k: row[k] for k in ("seq", "previous_sha256", "record")}
        if row["sha256"] != digest(body):
            raise ValueError("ledger record hash mismatch")
        previous = row["sha256"]
        records.append(row["record"])
    return records


class Journal:
    def __init__(self, path):
        self.stream = path.open("x", encoding="utf-8")
        self.seq, self.previous = 0, ZERO_HASH

    def append(self, record):
        body = {"seq": self.seq, "previous_sha256": self.previous, "record": record}
        row = {**body, "sha256": digest(body)}
        self.stream.write(canonical_json(row) + "\n")
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.seq += 1
        self.previous = row["sha256"]

    def close(self):
        self.stream.close()


def prepare_run(protocol, output, participant):
    plan = build_plan(protocol)
    validate_participant(participant)
    output = Path(output)
    # Snapshot source before creating run artifacts, so the run itself cannot dirty HEAD.
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    source = source_snapshot(output)
    write_json(output / "protocol.json", protocol)
    write_jsonl_gz(output / "design.jsonl.gz", plan)
    write_jsonl_gz(
        output / "requests.jsonl.gz",
        ({k: p[k] for k in ("order", "trial_id", "request_sha256", "request")} for p in plan),
    )
    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "experiment_version": VERSION,
        "run_id": str(uuid.uuid4()),
        "status": "prepared",
        "created_at": utcnow(),
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "protocol_sha256": digest(protocol),
        "participant": participant,
        "participant_sha256": digest(participant),
        "planned_trials": len(plan),
        "network_calls_made_by_harness": 0,
        "source_kind": "deterministic_offline_control"
        if participant["kind"] == "deterministic_control"
        else "external_unattested_import",
        "packet_sha256": {
            name: sha256(output / name)
            for name in ("protocol.json", "design.jsonl.gz", "requests.jsonl.gz")
        },
        **source,
    }
    write_json(output / "manifest.json", manifest)
    return manifest, plan


def checked_path(root, name):
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("artifact path escapes run directory")
    candidate = root / relative
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError("artifact symlink escapes run directory")
    return candidate


def load_packets(output):
    output = Path(output)
    manifest = strict_json((output / "manifest.json").read_text())
    if (
        manifest["manifest_version"] != MANIFEST_VERSION
        or manifest["experiment_version"] != VERSION
    ):
        raise ValueError("unsupported manifest version")
    validate_participant(manifest["participant"])
    if digest(manifest["participant"]) != manifest["participant_sha256"]:
        raise ValueError("participant identity hash mismatch")
    expected_source = (
        "deterministic_offline_control"
        if manifest["participant"]["kind"] == "deterministic_control"
        else "external_unattested_import"
    )
    if manifest["source_kind"] != expected_source or manifest["network_calls_made_by_harness"] != 0:
        raise ValueError("incorrect collection provenance")
    if set(manifest["packet_sha256"]) != {"protocol.json", "design.jsonl.gz", "requests.jsonl.gz"}:
        raise ValueError("packet inventory is incomplete")
    for name, expected in manifest["packet_sha256"].items():
        if sha256(checked_path(output, name)) != expected:
            raise ValueError(f"packet hash mismatch: {name}")
    required_source = {
        "themind/__init__.py",
        "themind/timing.py",
        "themind/timing_runner.py",
        "themind/timing_controls.py",
        "themind/timing_analysis.py",
        "themind/stage1.py",
        "themind/runner.py",
        "themind/engine.py",
        "themind/policies.py",
        "themind/analysis.py",
    }
    actual_source = {"themind/" + p.name for p in (output / "source" / "themind").glob("*.py")}
    if not required_source <= set(manifest["source_sha256"]) or actual_source != set(
        manifest["source_sha256"]
    ):
        raise ValueError("source inventory is incomplete or contains untracked modules")
    for name, expected in manifest["source_sha256"].items():
        if sha256(checked_path(output / "source", name)) != expected:
            raise ValueError(f"source hash mismatch: {name}")
    if not manifest["source_sha256"] or "themind/timing.py" not in manifest["source_sha256"]:
        raise ValueError("missing experiment source snapshot")
    protocol = strict_json((output / "protocol.json").read_text())
    if digest(protocol) != manifest["protocol_sha256"]:
        raise ValueError("protocol identity hash mismatch")
    plan = list(read_jsonl(output / "design.jsonl.gz"))
    if plan != build_plan(protocol):
        raise ValueError("frozen design differs from compiled protocol")
    requests = list(read_jsonl(output / "requests.jsonl.gz"))
    if requests != [
        {k: p[k] for k in ("order", "trial_id", "request_sha256", "request")} for p in plan
    ]:
        raise ValueError("request packet differs from frozen design")
    if manifest["planned_trials"] != len(plan):
        raise ValueError("incorrect planned trial count")
    return manifest, plan, protocol


def attempt_record(manifest, probe, started_at):
    return {
        "attempt_id": digest(
            {"run_id": manifest["run_id"], "trial_id": probe["trial_id"], "attempt_number": 1}
        ),
        "run_id": manifest["run_id"],
        "trial_id": probe["trial_id"],
        "request_sha256": probe["request_sha256"],
        "participant_sha256": manifest["participant_sha256"],
        "started_at": started_at,
    }


def result_record(attempt, response, completed_at, latency_seconds):
    return {
        **{k: v for k, v in attempt.items() if k != "started_at"},
        "completed_at": completed_at,
        "latency_seconds": latency_seconds,
        **response,
    }


def validate_records(manifest, plan, attempts, results):
    """One attempt per planned trial, no retry selection or provider substitution."""
    attempt_map = {}
    probes_by_trial = {p["trial_id"]: p for p in plan}
    for index, attempt in enumerate(attempts):
        exact_keys(attempt, ATTEMPT_KEYS, "attempt")
        if index >= len(plan):
            raise ValueError("more attempts than planned trials")
        expected = attempt_record(manifest, plan[index], attempt["started_at"])
        if attempt != expected:
            raise ValueError("attempt differs from frozen order/request/participant identity")
        timestamp(attempt["started_at"])
        if index and timestamp(attempt["started_at"]) < timestamp(
            attempts[index - 1]["started_at"]
        ):
            raise ValueError("attempt timestamps run backwards")
        if attempt["attempt_id"] in attempt_map:
            raise ValueError("duplicate attempt")
        attempt_map[attempt["attempt_id"]] = attempt
    result_map = {}
    for result in results:
        exact_keys(result, RESULT_KEYS, "result")
        attempt_id = result["attempt_id"]
        if attempt_id not in attempt_map or attempt_id in result_map:
            raise ValueError("unknown or duplicate result attempt")
        attempt = attempt_map[attempt_id]
        for key in ("run_id", "trial_id", "request_sha256", "participant_sha256"):
            if result[key] != attempt[key]:
                raise ValueError(f"result provenance mismatch: {key}")
        if timestamp(result["completed_at"]) < timestamp(attempt["started_at"]):
            raise ValueError("result completed before its attempt")
        if not finite(result["latency_seconds"]) or result["latency_seconds"] < 0:
            raise ValueError("latency must be finite and nonnegative")
        if result["status"] not in STATUSES:
            raise ValueError("unknown result status")
        if result["raw_text"] is not None and not isinstance(result["raw_text"], str):
            raise ValueError("raw_text must be string or null")
        if not isinstance(result["raw_response"], str) or not nonempty(result["finish_reason"]):
            raise ValueError("raw response and finish metadata required")
        if result["status"] == "success" and not isinstance(result["raw_text"], str):
            raise ValueError("successful transport must retain response text")
        if result["status"] != "provider_error" and not nonempty(result["model_returned"]):
            raise ValueError("returned model identity required")
        if result["model_returned"] is not None and not nonempty(result["model_returned"]):
            raise ValueError("invalid returned model identity")
        if result["provider_request_id"] is not None and not nonempty(
            result["provider_request_id"]
        ):
            raise ValueError("invalid provider request id")
        for key in ("input_tokens", "output_tokens"):
            if result[key] is not None and (type(result[key]) is not int or result[key] < 0):
                raise ValueError("token usage must be a nonnegative integer or null")
        if result["error"] is not None and not isinstance(result["error"], str):
            raise ValueError("error must be string or null")
        if result["status"] == "provider_error" and not nonempty(result["error"]):
            raise ValueError("provider error detail required")
        # Known truncation/refusal metadata cannot be relabeled successful JSON.
        if result["status"] == "success" and result["finish_reason"] in {
            "length",
            "max_tokens",
            "refusal",
            "content_filter",
            "error",
        }:
            raise ValueError("finish reason contradicts success status")
        if manifest["participant"]["kind"] == "deterministic_control":
            # A claimed deterministic fixture is reproducible, unlike an external
            # provider observation. Re-execute it from the request to verify the
            # raw response as well as the derived score, even if hashes are rebuilt.
            probe = probes_by_trial[attempt["trial_id"]]
            expected_response = control_response(
                manifest["participant"]["name"], probe["request"], probe["repetition"]
            )
            if any(result[key] != value for key, value in expected_response.items()):
                raise ValueError("offline control result does not replay from its request")
        result_map[attempt_id] = result
    return attempt_map, result_map


def derive_rows(manifest, plan, attempts, results):
    _, result_map = validate_records(manifest, plan, attempts, results)
    attempts_by_trial = {a["trial_id"]: a for a in attempts}
    rows = []
    for probe in plan:
        row = {k: v for k, v in probe.items() if k != "request"}
        row.update(
            participant=manifest["participant"]["name"],
            source_kind=manifest["source_kind"],
            normalized=None,
            score=None,
            parse_error=None,
        )
        attempt = attempts_by_trial.get(probe["trial_id"])
        result = result_map.get(attempt["attempt_id"]) if attempt else None
        row["status"] = (
            "not_attempted"
            if attempt is None
            else "missing_result"
            if result is None
            else result["status"]
        )
        row["attempt_id"] = attempt["attempt_id"] if attempt else None
        row["model_returned"] = result["model_returned"] if result else None
        for field in ("input_tokens", "output_tokens", "latency_seconds", "finish_reason"):
            row[field] = result[field] if result else None
        if (
            result
            and result["status"] == "success"
            and result["model_returned"] != manifest["participant"]["model_requested"]
        ):
            row["status"] = "model_mismatch"
        elif result and result["status"] == "success":
            s, r = Snapshot(**probe["snapshot"]), Representation(**probe["representation"])
            try:
                normalized = parse_response(result["raw_text"], probe["interface"], s, r)
            except ValueError as exc:
                row.update(status="invalid_schema", parse_error=str(exc))
            else:
                row.update(
                    status="valid",
                    normalized=normalized,
                    score=score_response(normalized, s, probe["interface"]),
                )
        rows.append(row)
    return rows


def finalize_run(output, *, allow_partial=False):
    output = Path(output)
    manifest, plan, protocol = load_packets(output)
    if manifest["status"] not in {"prepared", "running", "aborted"}:
        raise ValueError("sealed runs cannot be overwritten")
    attempts = read_chain(output / "attempts.jsonl")
    results = read_chain(output / "results.jsonl")
    rows = derive_rows(manifest, plan, attempts, results)
    complete = len(attempts) == len(plan) and len(results) == len(attempts)
    if not complete and not allow_partial:
        raise ValueError("incomplete attempt/result coverage")
    from themind.timing_analysis import render_report, summarize

    summary = summarize(rows, protocol, manifest)
    with _atomic_derived_file(output / "summary.json") as stream:
        stream.write((json.dumps(summary, indent=2, allow_nan=False) + "\n").encode())
    with _atomic_derived_file(output / "report.md") as stream:
        stream.write(render_report(summary).encode())
    with _atomic_derived_file(output / "scored.jsonl.gz") as stream:
        _write_jsonl_gz_stream(stream, rows)
    manifest.update(
        status="complete" if complete else "incomplete",
        completed_at=utcnow(),
        attempts=len(attempts),
        results=len(results),
    )
    manifest["artifact_sha256"] = {
        name: sha256(output / name)
        for name in (
            "attempts.jsonl",
            "results.jsonl",
            "scored.jsonl.gz",
            "summary.json",
            "report.md",
        )
    }
    write_json(output / "manifest.json", manifest)
    return summary


def verify_run(output):
    output = Path(output)
    manifest, plan, protocol = load_packets(output)
    if manifest["status"] not in {"complete", "incomplete"}:
        raise ValueError("run is not sealed; inspect or finalize its partial journal")
    required = {"attempts.jsonl", "results.jsonl", "scored.jsonl.gz", "summary.json", "report.md"}
    if set(manifest["artifact_sha256"]) != required:
        raise ValueError("sealed artifact inventory is incomplete")
    for name, expected in manifest["artifact_sha256"].items():
        if sha256(checked_path(output, name)) != expected:
            raise ValueError(f"artifact hash mismatch: {name}")
    attempts, results = read_chain(output / "attempts.jsonl"), read_chain(output / "results.jsonl")
    rows = derive_rows(manifest, plan, attempts, results)
    if rows != list(read_jsonl(output / "scored.jsonl.gz")):
        raise ValueError("derived scores differ from raw response evidence")
    complete = len(attempts) == len(plan) and len(results) == len(attempts)
    if (
        (manifest["status"] == "complete") != complete
        or manifest["attempts"] != len(attempts)
        or manifest["results"] != len(results)
    ):
        raise ValueError("manifest completion/count claims are incorrect")
    from themind.timing_analysis import render_report, summarize

    summary = summarize(rows, protocol, manifest)
    if (
        summary != strict_json((output / "summary.json").read_text())
        or render_report(summary) != (output / "report.md").read_text()
    ):
        raise ValueError("analysis/report differs from validated response evidence")
    return summary


def run_control(protocol, output, name, *, responder=None):
    manifest, plan = prepare_run(protocol, output, descriptor(name))
    output = Path(output)
    manifest["status"] = "running"
    write_json(output / "manifest.json", manifest)
    attempts, results = Journal(output / "attempts.jsonl"), Journal(output / "results.jsonl")
    try:
        for probe in plan:
            started = utcnow()
            attempt = attempt_record(manifest, probe, started)
            attempts.append(attempt)  # durable before invoking even an offline responder
            start = time.monotonic()
            response = (responder or control_response)(name, probe["request"], probe["repetition"])
            results.append(result_record(attempt, response, utcnow(), time.monotonic() - start))
    except BaseException as exc:
        manifest.update(
            status="aborted",
            error_type=type(exc).__name__,
            attempts=attempts.seq,
            results=results.seq,
        )
        write_json(output / "manifest.json", manifest)
        raise
    finally:
        attempts.close()
        results.close()
    return finalize_run(output)


def import_external(output, attempt_file, result_file, *, allow_partial=False):
    """Import exact collector evidence; never synthesize attempts from response rows."""
    output = Path(output)
    manifest, plan, _ = load_packets(output)
    if manifest["participant"]["kind"] != "external" or manifest["status"] != "prepared":
        raise ValueError("imports require an unused external request packet")
    attempts, results = read_chain(Path(attempt_file)), read_chain(Path(result_file))
    validate_records(manifest, plan, attempts, results)
    if not allow_partial and (len(attempts) != len(plan) or len(results) != len(attempts)):
        raise ValueError("incomplete external evidence; use allow_partial to label it explicitly")
    for source, name in ((attempt_file, "attempts.jsonl"), (result_file, "results.jsonl")):
        with (output / name).open("xb") as stream:
            stream.write(Path(source).read_bytes())
    return finalize_run(output, allow_partial=allow_partial)
