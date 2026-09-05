import copy
import hashlib
import json
from unittest.mock import patch

import pytest

from themind.runner import run_suite, validate_suite


def suite():
    return {
        "name": "test",
        "seeds": [10, 11],
        "config": {"players": 2, "cards_per_player": 2},
        "conditions": [
            {"name": name, "policies": [{"kind": "proportional"}] * 2} for name in ("a", "b")
        ],
        "contrasts": {"paired": {"a": 1, "b": -1}},
    }


@pytest.mark.asyncio
async def test_complete_artifacts_and_no_overwrite(tmp_path):
    output = tmp_path / "run"
    result = await run_suite(suite(), output)
    assert result["conditions"]["a"]["successes"] == 2
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "complete"
    for name, digest in manifest["artifact_sha256"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest
    for name, digest in manifest["source_sha256"].items():
        assert hashlib.sha256((output / "source" / name).read_bytes()).hexdigest() == digest
    rows = [json.loads(line) for line in (output / "rounds.jsonl").read_text().splitlines()]
    assert rows[0]["hands"] == rows[1]["hands"]
    before = (output / "rounds.jsonl").read_bytes()
    with pytest.raises(FileExistsError):
        await run_suite(suite(), output)
    assert (output / "rounds.jsonl").read_bytes() == before


@pytest.mark.parametrize(
    "change",
    [
        lambda s: s.pop("name"),
        lambda s: s["conditions"][0].update(name=None),
        lambda s: s["contrasts"]["paired"].update(b=1),
        lambda s: s["contrasts"]["paired"].update(b=float("nan")),
        lambda s: s["conditions"][1].update(config={"cards_per_player": 3}),
        lambda s: s["conditions"][1]["policies"][0].update(scale=-1),
        lambda s: s["conditions"][1]["policies"][0].update(unknown=True),
        lambda s: s["seeds"].append(10),
    ],
)
@pytest.mark.asyncio
async def test_invalid_suite_fails_before_any_round(tmp_path, change):
    config = copy.deepcopy(suite())
    change(config)
    with patch("themind.runner.run_round") as mocked:
        with pytest.raises((ValueError, TypeError)):
            await run_suite(config, tmp_path / "bad")
        mocked.assert_not_called()
    assert not (tmp_path / "bad").exists()


@pytest.mark.asyncio
async def test_network_budget_requires_opt_in_and_is_conservative(tmp_path):
    config = suite()
    config["conditions"][0]["policies"] = [{"kind": "openai", "model": "fake"}] * 2
    config["conditions"][0]["config"] = {"mode": "feedback"}
    assert validate_suite(config) == 16
    for kwargs in ({}, {"allow_network": True, "max_requests": 15}):
        with patch("themind.runner.run_round") as mocked:
            with pytest.raises(ValueError):
                await run_suite(config, tmp_path / "blocked", **kwargs)
            mocked.assert_not_called()


@pytest.mark.asyncio
async def test_unexpected_failure_marks_run_aborted(tmp_path):
    with patch("themind.runner.run_round", side_effect=RuntimeError("programming bug")):
        with pytest.raises(RuntimeError):
            await run_suite(suite(), tmp_path / "aborted")
    manifest = json.loads((tmp_path / "aborted" / "manifest.json").read_text())
    assert manifest["status"] == "aborted"
    assert not (tmp_path / "aborted" / "summary.json").exists()
