import json
from pathlib import Path

import pytest

from themind.timing_validation import run_validation, verify_validation


def test_control_validation_bundle_reproduces_and_rejects_changed_index(tmp_path):
    p = json.loads(Path("experiments/stage1-pilot.json").read_text())
    p.update(repetitions=1, free_repetitions=3, units=["seconds", "milliseconds"])
    p["cases"] = [p["cases"][0], p["cases"][-2], p["cases"][-1]]
    p["cases"][0]["times"] = [19.5, 20, 20.5, 30.5]
    p["cases"][1]["times"] = [0, 30]
    p["cases"][2]["times"] = [0, 15, 30]
    output = tmp_path / "validation"
    index = run_validation(p, output)
    assert all(index["checks"].values())
    assert index["model_calls"] == 0
    assert index["total_control_responses"] == index["requests_per_control"] * 7
    assert verify_validation(output) == index
    with pytest.raises(FileExistsError):
        run_validation(p, output)
    index["checks"]["oracle:prescribed_compliance"] = False
    (output / "validation.json").write_text(json.dumps(index))
    with pytest.raises(ValueError, match="checks differ"):
        verify_validation(output)
