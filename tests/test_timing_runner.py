import copy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from themind.timing import digest
from themind.timing_controls import control_response, descriptor
from themind.timing_runner import (
    Journal,
    attempt_record,
    chain_rows,
    derive_rows,
    finalize_run,
    import_external,
    load_packets,
    prepare_run,
    read_chain,
    result_record,
    run_control,
    validate_records,
    verify_run,
)


def small_protocol():
    p = json.loads(Path("experiments/stage1-pilot.json").read_text())
    p.update(
        repetitions=1, free_repetitions=3, units=["seconds"], directions=["elapsed"], origins=[0]
    )
    p["cases"] = [p["cases"][0], p["cases"][-2], p["cases"][-1]]
    p["cases"][0]["times"] = [10, 20, 30.5]
    p["cases"][1]["times"] = [0, 30]
    p["cases"][2]["times"] = [0, 15, 30]
    return p


def external():
    return {
        "kind": "external",
        "name": "recorded-fixture",
        "provider": "fixture-provider",
        "model_requested": "fixture-model-v1",
        "settings": {
            "temperature": 0,
            "max_output_tokens": 100,
            "structured_output": True,
            "adapter_version": "fixture-v1",
        },
    }


def records(manifest, plan):
    attempts = [attempt_record(manifest, p, "2026-09-07T20:00:00+00:00") for p in plan]
    results = []
    for a, p in zip(attempts, plan):
        response = control_response("oracle", p["request"], p["repetition"])
        response["model_returned"] = manifest["participant"]["model_requested"]
        results.append(result_record(a, response, "2026-09-07T20:00:01+00:00", 1))
    return attempts, results


def write_chain(path, data):
    path.write_text("".join(json.dumps(r) + "\n" for r in chain_rows(data)))


def test_oracle_run_reproduces_control_outcomes_and_verifies_all_artifacts(tmp_path):
    p = small_protocol()
    with patch("urllib.request.urlopen", side_effect=AssertionError("network called")):
        summary = run_control(p, tmp_path / "a", "oracle")
        second = run_control(p, tmp_path / "b", "oracle")
    assert summary["counts"] == second["counts"]
    assert summary["paired_contrasts"] == second["paired_contrasts"]
    assert summary["free_policy_curves"] == second["free_policy_curves"]
    assert summary["instrument_checks"]["all_prescribed_snapshots_compliant"] is True
    assert verify_run(tmp_path / "a") == summary
    for name in ("design.jsonl.gz", "requests.jsonl.gz"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()
    manifest, plan, _ = load_packets(tmp_path / "a")
    assert len(read_chain(tmp_path / "a" / "attempts.jsonl")) == len(plan)
    assert manifest["network_calls_made_by_harness"] == 0
    assert manifest["status"] == "complete"
    before = (tmp_path / "a" / "results.jsonl").read_bytes()
    with pytest.raises(FileExistsError):
        run_control(p, tmp_path / "a", "oracle")
    with pytest.raises(ValueError, match="sealed"):
        finalize_run(tmp_path / "a")
    assert (tmp_path / "a" / "results.jsonl").read_bytes() == before


@pytest.mark.parametrize(
    "name,status",
    [
        ("invalid_json", "invalid_schema"),
        ("refusal", "refusal"),
        ("truncated", "truncated"),
        ("provider_error", "provider_error"),
    ],
)
def test_failures_do_not_become_behavioral_waits_or_fake_moves(tmp_path, name, status):
    summary = run_control(small_protocol(), tmp_path / name, name)
    assert summary["counts"]["statuses"] == {status: summary["counts"]["planned"]}
    assert summary["counts"]["valid"] == 0
    assert summary["counts"]["valid_only_compliance"] is None
    assert summary["counts"]["correct_wait"] == 0
    assert summary["never_snapshot_sets"]["all_snapshots_valid"] == 0
    assert verify_run(tmp_path / name) == summary
    for curve in summary["free_policy_curves"]:
        assert all(p["q"] is None and p["F_absolute"] is None for p in curve["points"])


def test_interrupted_attempt_persisted_before_responder_and_partial_denominators(tmp_path):
    output = tmp_path / "aborted"
    calls = 0

    def fail(name, request, repetition):
        nonlocal calls
        calls += 1
        assert len(read_chain(output / "attempts.jsonl")) == calls
        if calls == 3:
            raise RuntimeError("intentional offline interruption")
        return control_response(name, request, repetition)

    with pytest.raises(RuntimeError):
        run_control(small_protocol(), output, "oracle", responder=fail)
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "aborted"
    assert manifest["attempts"] == 3 and manifest["results"] == 2
    assert not (output / "summary.json").exists()
    with pytest.raises(ValueError, match="incomplete"):
        finalize_run(output)
    summary = finalize_run(output, allow_partial=True)
    assert summary["counts"]["attempted"] == 3
    assert summary["counts"]["statuses"]["missing_result"] == 1
    assert summary["counts"]["statuses"]["not_attempted"] == summary["counts"]["planned"] - 3
    assert verify_run(output) == summary
    assert json.loads((output / "manifest.json").read_text())["status"] == "incomplete"


@pytest.mark.parametrize(
    "change",
    [
        lambda a, r: a.append(copy.deepcopy(a[0])),
        lambda a, r: a.reverse(),
        lambda a, r: r.append(copy.deepcopy(r[0])),
        lambda a, r: r[0].update(attempt_id="unknown"),
        lambda a, r: r[0].update(request_sha256="forged"),
        lambda a, r: r[0].update(participant_sha256="other-model-settings"),
        lambda a, r: r[0].update(run_id="other-run"),
        lambda a, r: r[0].update(trial_id="other-snapshot"),
        lambda a, r: r[0].update(input_tokens=True),
        lambda a, r: r[0].update(output_tokens=-1),
        lambda a, r: r[0].update(latency_seconds=float("nan")),
        lambda a, r: r[0].update(completed_at="2026-09-07T20:00:01"),
        lambda a, r: r[0].update(completed_at="2026-09-07T19:00:00Z"),
        lambda a, r: r[0].update(finish_reason="length"),
        lambda a, r: r[0].update(raw_response=None),
        lambda a, r: r[0].update(model_returned=None),
        lambda a, r: r[0].update(status="timeout"),
        lambda a, r: r[0].update(extra="untracked"),
    ],
)
def test_provenance_and_metadata_fail_closed(tmp_path, change):
    manifest, plan = prepare_run(small_protocol(), tmp_path / "packet", external())
    attempts, results = records(manifest, plan)
    change(attempts, results)
    with pytest.raises(ValueError):
        validate_records(manifest, plan, attempts, results)


def test_returned_model_mismatch_is_retained_but_not_behaviorally_scored(tmp_path):
    manifest, plan = prepare_run(small_protocol(), tmp_path / "packet", external())
    attempts, results = records(manifest, plan)
    results[0]["model_returned"] = "different-model"
    rows = derive_rows(manifest, plan, attempts, results)
    assert rows[0]["status"] == "model_mismatch"
    assert rows[0]["normalized"] is None and rows[0]["score"] is None
    assert rows[0]["model_returned"] == "different-model"


def test_import_requires_independent_exact_attempt_evidence_and_preserves_raw_bytes(tmp_path):
    output = tmp_path / "packet"
    manifest, plan = prepare_run(small_protocol(), output, external())
    attempts, results = records(manifest, plan)
    # Complete presentation wrapper remains invalid, not stripped or rescued.
    results[0]["raw_text"] = "```json\n" + results[0]["raw_text"] + "\n```"
    source_attempts, source_results = tmp_path / "attempts.jsonl", tmp_path / "results.jsonl"
    write_chain(source_attempts, attempts)
    write_chain(source_results, results)
    summary = import_external(output, source_attempts, source_results)
    assert summary["source_kind"] == "external_unattested_import"
    assert summary["counts"]["statuses"]["invalid_schema"] == 1
    assert (output / "attempts.jsonl").read_bytes() == source_attempts.read_bytes()
    assert (output / "results.jsonl").read_bytes() == source_results.read_bytes()
    assert verify_run(output) == summary
    with pytest.raises(ValueError, match="unused"):
        import_external(output, source_attempts, source_results)


@pytest.mark.parametrize(
    "artifact",
    [
        "requests.jsonl.gz",
        "design.jsonl.gz",
        "protocol.json",
        "source/themind/timing.py",
        "results.jsonl",
        "attempts.jsonl",
        "summary.json",
        "report.md",
        "scored.jsonl.gz",
    ],
)
def test_altered_artifact_rejected(tmp_path, artifact):
    output = tmp_path / "run"
    run_control(small_protocol(), output, "oracle")
    with (output / artifact).open("ab") as stream:
        stream.write(b"\n ")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_run(output)


def test_recomputed_outer_hash_cannot_hide_changed_scores(tmp_path):
    from themind.runner import sha256

    output = tmp_path / "run"
    run_control(small_protocol(), output, "oracle")
    summary = json.loads((output / "summary.json").read_text())
    summary["counts"]["compliant"] += 10
    (output / "summary.json").write_text(json.dumps(summary))
    manifest = json.loads((output / "manifest.json").read_text())
    manifest["artifact_sha256"]["summary.json"] = sha256(output / "summary.json")
    (output / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="analysis/report"):
        verify_run(output)


def test_modified_ledger_or_reordered_lines_break_chain(tmp_path):
    p = tmp_path / "journal.jsonl"
    journal = Journal(p)
    journal.append({"raw_text": "first"})
    journal.append({"raw_text": "second"})
    journal.close()
    rows = p.read_text().splitlines()
    p.write_text("\n".join(reversed(rows)) + "\n")
    with pytest.raises(ValueError, match="chain"):
        read_chain(p)
    data = json.loads(rows[0])
    data["record"]["raw_text"] = "modified"
    p.write_text(json.dumps(data) + "\n")
    with pytest.raises(ValueError, match="hash"):
        read_chain(p)


def test_missing_results_cannot_claim_completion_even_with_rehashed_manifest(tmp_path):
    output = tmp_path / "packet"
    manifest, plan = prepare_run(small_protocol(), output, external())
    attempts, results = records(manifest, plan)
    write_chain(output / "attempts.jsonl", attempts)
    write_chain(output / "results.jsonl", results[:-1])
    finalize_run(output, allow_partial=True)
    manifest = json.loads((output / "manifest.json").read_text())
    manifest["status"] = "complete"
    (output / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="completion/count"):
        verify_run(output)


def test_secrets_control_spoofing_and_bad_budget_rejected_before_output(tmp_path):
    output = tmp_path / "bad"
    participant = external()
    participant["settings"]["nested"] = {"authorization": "do-not-log"}
    with pytest.raises(ValueError, match="credentials"):
        prepare_run(small_protocol(), output, participant)
    assert not output.exists()
    participant = descriptor("oracle")
    participant["settings"]["version"] = "forged"
    with pytest.raises(ValueError, match="identity"):
        prepare_run(small_protocol(), output, participant)
    assert not output.exists()
    p = small_protocol()
    p["max_requests_per_participant"] = 1
    with pytest.raises(ValueError, match="budget"):
        prepare_run(p, output, external())
    assert not output.exists()


def test_packet_inventory_cannot_silently_drop_request_hash(tmp_path):
    output = tmp_path / "run"
    prepare_run(small_protocol(), output, external())
    manifest = json.loads((output / "manifest.json").read_text())
    manifest["packet_sha256"].pop("requests.jsonl.gz")
    (output / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="inventory"):
        load_packets(output)


def test_hashes_link_identical_prompts_to_distinct_replicate_attempts(tmp_path):
    p = small_protocol()
    p["repetitions"] = 2
    manifest, plan = prepare_run(p, tmp_path / "run", external())
    repeated = [r for r in plan if r["request_sha256"] == plan[0]["request_sha256"]]
    assert len(repeated) > 1
    assert len({r["trial_id"] for r in repeated}) == len(repeated)
    assert len(
        {attempt_record(manifest, r, "2026-09-07T20:00:00Z")["attempt_id"] for r in repeated}
    ) == len(repeated)
    assert manifest["participant_sha256"] == digest(external())


def test_claimed_offline_control_raw_result_must_replay_even_after_rehashing(tmp_path):
    from themind.runner import sha256

    output = tmp_path / "run"
    run_control(small_protocol(), output, "oracle")
    original = read_chain(output / "results.jsonl")
    original[0]["raw_text"] = '{"play":true}'
    original[0]["raw_response"] = '{"forged":true}'
    write_chain(output / "results.jsonl", original)
    manifest = json.loads((output / "manifest.json").read_text())
    manifest["artifact_sha256"]["results.jsonl"] = sha256(output / "results.jsonl")
    (output / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="does not replay"):
        verify_run(output)


def test_source_hash_inventory_cannot_omit_an_executable_module(tmp_path):
    output = tmp_path / "run"
    prepare_run(small_protocol(), output, external())
    manifest = json.loads((output / "manifest.json").read_text())
    manifest["source_sha256"].pop("themind/timing_analysis.py")
    (output / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="source inventory"):
        load_packets(output)


@pytest.mark.parametrize("interruption", ["gzip_write", "manifest_seal"])
@pytest.mark.parametrize("partial", [False, True])
@pytest.mark.parametrize("existing_score", [False, True])
def test_interrupted_finalization_retries_without_changing_raw_evidence(
    tmp_path, interruption, partial, existing_score
):
    import gzip

    from themind.timing_runner import read_jsonl, write_json

    output = tmp_path / "unsealed"
    manifest, plan = prepare_run(small_protocol(), output, external())
    attempts, results = records(manifest, plan)
    if partial:
        attempts, results = attempts[:3], results[:2]
    write_chain(output / "attempts.jsonl", attempts)
    write_chain(output / "results.jsonl", results)
    manifest["status"] = "aborted" if partial else "running"
    write_json(output / "manifest.json", manifest)
    before_manifest = (output / "manifest.json").read_bytes()
    raw_names = (
        "attempts.jsonl",
        "results.jsonl",
        "protocol.json",
        "design.jsonl.gz",
        "requests.jsonl.gz",
    )
    raw_bytes = {name: (output / name).read_bytes() for name in raw_names}
    score = output / "scored.jsonl.gz"
    old_score = b"\x1f\x8b\x08previous interrupted score"
    if existing_score:
        score.write_bytes(old_score)
    # A SIGKILL may leave a temporary that normal exception cleanup cannot remove.
    stale_temporary = output / ".scored.jsonl.gz.orphan.tmp"
    stale_temporary.write_bytes(b"previous temporary fragment")
    gzip_write = gzip.GzipFile.write
    reached_interruption = []

    def interrupt_gzip(zipped, data):
        written = gzip_write(zipped, data)
        if "scored.jsonl.gz" in Path(zipped.fileobj.name).name:
            zipped.flush()
            reached_interruption.append(True)
            raise OSError("injected interruption during score gzip writing")
        return written

    def interrupt_seal(path, value):
        if path.name == "manifest.json" and value.get("status") in {"complete", "incomplete"}:
            # The completed score exists, but the durable manifest is still unsealed.
            assert len(list(read_jsonl(score))) == len(plan)
            reached_interruption.append(True)
            raise OSError("injected interruption before manifest seal")
        return write_json(path, value)

    failure = (
        patch("themind.timing_runner.gzip.GzipFile.write", new=interrupt_gzip)
        if interruption == "gzip_write"
        else patch("themind.timing_runner.write_json", side_effect=interrupt_seal)
    )
    with failure, pytest.raises(OSError, match="injected interruption"):
        finalize_run(output, allow_partial=partial)
    assert reached_interruption == [True]
    assert (output / "manifest.json").read_bytes() == before_manifest
    assert {name: (output / name).read_bytes() for name in raw_names} == raw_bytes
    if interruption == "gzip_write":
        if existing_score:
            assert score.read_bytes() == old_score  # no partial replacement exposed
        else:
            assert not score.exists()
    assert set(output.glob(".scored.jsonl.gz.*.tmp")) == {stale_temporary}

    summary = finalize_run(output, allow_partial=partial)
    assert verify_run(output) == summary
    assert {name: (output / name).read_bytes() for name in raw_names} == raw_bytes
    sealed = json.loads((output / "manifest.json").read_text())
    assert sealed["status"] == ("incomplete" if partial else "complete")
    assert sealed["attempts"] == len(attempts)
    assert sealed["results"] == len(results)
    assert stale_temporary.read_bytes() == b"previous temporary fragment"

    # Both complete and explicitly incomplete seals prohibit all derived rewriting.
    sealed_names = (*raw_names, "scored.jsonl.gz", "summary.json", "report.md", "manifest.json")
    sealed_bytes = {name: (output / name).read_bytes() for name in sealed_names}
    with patch("themind.timing_runner._atomic_derived_file") as writer:
        with pytest.raises(ValueError, match="sealed runs"):
            finalize_run(output, allow_partial=True)
        writer.assert_not_called()
    assert {name: (output / name).read_bytes() for name in sealed_names} == sealed_bytes


def test_raw_packet_and_journal_creation_stays_exclusive(tmp_path):
    from themind.timing_runner import write_jsonl_gz

    packet = tmp_path / "requests.jsonl.gz"
    write_jsonl_gz(packet, [{"request": "original"}])
    before = packet.read_bytes()
    with pytest.raises(FileExistsError):
        write_jsonl_gz(packet, [{"request": "replacement"}])
    assert packet.read_bytes() == before

    path = tmp_path / "attempts.jsonl"
    journal = Journal(path)
    journal.append({"attempt": "original"})
    journal.close()
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        Journal(path)
    assert path.read_bytes() == before
