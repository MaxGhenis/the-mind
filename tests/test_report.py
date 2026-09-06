import json
from html.parser import HTMLParser

from themind.report import render_report


class ReportParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.tags = []
        self.current_script = None

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag == "script":
            self.current_script = {"attrs": dict(attrs), "text": ""}
            self.scripts.append(self.current_script)

    def handle_endtag(self, tag):
        if tag == "script":
            self.current_script = None

    def handle_data(self, data):
        if self.current_script is not None:
            self.current_script["text"] += data


def example(name="pilot", policy="proportional"):
    condition = {
        "attempted": 2,
        "valid": 1,
        "successes": 1,
        "status_counts": {"success": 1, "invalid_response": 1},
        "completion_rate_all_attempts": 0.5,
        "completion_ci95_all_attempts": [0.095, 0.905],
        "completion_rate_valid_only": 1.0,
        "completion_ci95_valid_only": [0.207, 1],
        "infrastructure_failure_rate": 0.5,
        "mean_correct_prefix": 1,
        "mean_collisions": 0,
    }
    summary = {
        "name": name,
        "conditions": {name: condition},
        "contrasts": {
            name: {
                "weights": {name: 1, "comparison": -1},
                "paired_deals": 2,
                "blocks_with_infrastructure_failure": 1,
                "difference_all_attempts": -0.5,
                "paired_bootstrap_ci95": [-1, 0],
            }
        },
    }
    record = {"condition": name, "seed": 1, "status": "success", "plays": []}
    suite = {
        "name": name,
        "notes": name,
        "conditions": [{"name": name, "policies": [{"kind": policy}]}],
    }
    return summary, [record], suite


def test_counts_denominators_intervals_and_baseline_scope():
    report = render_report(*example())
    assert "1 / 2" in report
    assert "1 invalid" in report
    assert "50.0%" in report
    assert "100.0%" in report
    assert "[9.5%, 90.5%]" in report
    assert "-50.0 pp" in report
    assert "[-100.0, +0.0] pp" in report
    assert "no language models evaluated" in report
    assert "API response latency is never plotted" in report


def test_untrusted_names_and_model_output_cannot_break_out_of_json():
    attack = '</script><script src="https://evil.example/run.js"></script><img src=x onerror=alert(1)>__PAYLOAD__'
    summary, records, suite = example(attack)
    records[0]["decisions"] = [{"metadata": {"response": attack + "\u2028"}}]
    report = render_report(summary, records, suite)
    parsed = ReportParser()
    parsed.feed(report)
    assert len(parsed.scripts) == 2
    assert not any(tag == "img" for tag, _ in parsed.tags)
    assert not any("src" in script["attrs"] for script in parsed.scripts)
    embedded = next(
        script for script in parsed.scripts if script["attrs"].get("id") == "report-data"
    )
    decoded = json.loads(embedded["text"])
    assert decoded["records"][0]["decisions"][0]["metadata"]["response"] == attack + "\u2028"
    assert "\\u003c/script\\u003e" in embedded["text"]
    assert "&lt;img src=x onerror=alert(1)&gt;__PAYLOAD__" in report
    assert "innerHTML" not in report


def test_model_pilot_is_not_labeled_as_baseline_only():
    report = render_report(*example(policy="openai"))
    assert "no language models evaluated" not in report
    assert "results apply to this configured sample" in report


def test_missing_intervals_and_no_contrasts_are_renderable():
    summary, records, suite = example()
    summary["conditions"]["pilot"]["completion_rate_valid_only"] = None
    summary["conditions"]["pilot"]["completion_ci95_valid_only"] = None
    summary["contrasts"] = {}
    report = render_report(summary, [], suite)
    assert "not available" in report
    assert 'id="contrasts-heading"' not in report
