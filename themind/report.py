"""Standalone, offline HTML reports for auditable coordination pilots."""

import html
import json
import re


def _escape(value):
    return html.escape(str(value), quote=True)


def _percent(value):
    return "—" if value is None else f"{value * 100:.1f}%"


def _interval(value, *, points=False):
    if value is None:
        return "not available"
    if points:
        return f"[{value[0] * 100:+.1f}, {value[1] * 100:+.1f}] pp"
    return f"[{value[0] * 100:.1f}%, {value[1] * 100:.1f}%]"


def _condition_rows(conditions):
    rows = []
    for name, data in conditions.items():
        statuses = ", ".join(
            f"{key}: {value}" for key, value in sorted(data["status_counts"].items())
        )
        rows.append(
            "<tr>"
            f'<th scope="row">{_escape(name)}<small>{_escape(statuses)}</small></th>'
            f"<td>{data['successes']} / {data['attempted']}</td>"
            f'<td class="rate">{_percent(data["completion_rate_all_attempts"])}'
            f"<small>{_interval(data['completion_ci95_all_attempts'])}</small></td>"
            f"<td>{data['valid']}<small>{data['attempted'] - data['valid']} invalid</small></td>"
            f"<td>{_percent(data['completion_rate_valid_only'])}"
            f"<small>{_interval(data['completion_ci95_valid_only'])}</small></td>"
            f"<td>{_percent(data['infrastructure_failure_rate'])}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def _contrast_rows(contrasts):
    rows = []
    for name, data in contrasts.items():
        formula = "; ".join(
            f"{weight:+g} × {condition}" for condition, weight in data["weights"].items()
        )
        difference = data["difference_all_attempts"]
        estimate = "—" if difference is None else f"{difference * 100:+.1f} pp"
        rows.append(
            "<tr>"
            f'<th scope="row">{_escape(name)}<small>{_escape(formula)}</small></th>'
            f'<td class="rate">{estimate}</td>'
            f"<td>{_interval(data['paired_bootstrap_ci95'], points=True)}</td>"
            f"<td>{data['paired_deals']}</td>"
            f"<td>{data['blocks_with_infrastructure_failure']}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_report(summary, records, suite):
    """Render results without remote assets, executable model text, or invented data."""
    policies = [policy for condition in suite["conditions"] for policy in condition["policies"]]
    baseline_only = bool(policies) and all(
        p["kind"] in {"proportional", "random"} for p in policies
    )
    scope = (
        "Baseline validation pilot · no language models evaluated"
        if baseline_only
        else "Coordination research pilot · results apply to this configured sample"
    )
    explanation = (
        "These results test the simulator with programmed timing policies. "
        "They provide no empirical evidence about frontier-model coordination."
        if baseline_only
        else "This pilot evaluates the policies specified below. Results depend on the sampled "
        "models, prompts, deals, timing rules, and inference settings."
    )
    payload = json.dumps(
        {"records": list(records), "suite": suite}, ensure_ascii=True, allow_nan=False
    )
    # JSON script elements are raw-text HTML: escape '<' to prevent an embedded
    # '</script>' from terminating the element, even in model output or a name.
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    contrast_section = ""
    if summary.get("contrasts"):
        contrast_section = (
            """
<section aria-labelledby="contrasts-heading">
  <div class="section-label">02 / Paired comparisons</div>
  <h2 id="contrasts-heading">Completion differences</h2>
  <p class="caption">Weighted contrasts on the same deals, using all attempts. Estimates and 95% paired bootstrap intervals are in percentage points (pp).</p>
  <div class="table-scroll"><table>
    <thead><tr><th scope="col">Contrast and weights</th><th scope="col">Difference</th><th scope="col">95% interval</th><th scope="col">Paired deals</th><th scope="col">Deals with an<br>infrastructure failure</th></tr></thead>
    <tbody>"""
            + _contrast_rows(summary["contrasts"])
            + """</tbody>
  </table></div>
  <p class="caption">A narrow or zero-width pilot bootstrap interval can reflect too few observed outcome patterns; it is not proof of certainty.</p>
</section>"""
        )
    document = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>__TITLE__ · The Mind</title>
<style>
:root { color-scheme: light; --paper:#f7f7f2; --ink:#192d39; --muted:#52636b; --rule:#ced5d2; --accent:#176c66; }
* { box-sizing:border-box; } body { margin:0; background:var(--paper); color:var(--ink); font:16px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
main { max-width:1220px; margin:0 auto; padding:52px 46px 64px; } a { color:var(--accent); }
header { border-top:5px solid var(--ink); padding-top:24px; margin-bottom:44px; }
.masthead { display:flex; justify-content:space-between; gap:24px; align-items:baseline; font-size:13px; letter-spacing:.09em; text-transform:uppercase; }
.brand { font-size:18px; font-weight:750; letter-spacing:.16em; } .scope { color:var(--accent); }
h1 { font-family:Georgia,"Times New Roman",serif; font-size:clamp(30px,4vw,48px); font-weight:400; line-height:1.15; letter-spacing:-.02em; margin:34px 0 14px; overflow-wrap:anywhere; }
.lede { max-width:850px; font-size:18px; margin:0 0 14px; } .notes { color:var(--muted); white-space:pre-wrap; }
section { border-top:1px solid var(--rule); padding-top:25px; margin-top:40px; }
.section-label { color:var(--accent); font-size:12px; font-weight:650; text-transform:uppercase; letter-spacing:.1em; }
h2 { font-size:25px; font-weight:620; letter-spacing:-.025em; margin:9px 0 12px; } p { margin:10px 0; }
.caption, small { color:var(--muted); font-size:13px; line-height:1.5; } .caption { max-width:970px; }
.table-scroll { overflow-x:auto; margin-top:23px; } table { width:100%; border-collapse:collapse; font-variant-numeric:tabular-nums; font-size:14px; }
thead { border-bottom:1px solid var(--ink); } th,td { padding:16px 18px 16px 0; text-align:left; vertical-align:top; }
thead th { font-size:12px; font-weight:650; white-space:nowrap; } tbody tr { border-bottom:1px solid var(--rule); } tbody th { max-width:340px; min-width:180px; font-weight:600; overflow-wrap:anywhere; }
td { white-space:nowrap; } small { display:block; font-weight:400; margin-top:5px; } .rate { font-weight:680; color:var(--accent); }
.selector { display:grid; grid-template-columns:1fr 1fr; gap:20px; margin:24px 0 20px; }
label { display:block; font-size:12px; font-weight:650; margin-bottom:7px; }
select { width:100%; background:var(--paper); color:var(--ink); border:1px solid #84918f; border-radius:3px; padding:11px 12px; font:inherit; cursor:pointer; }
select:focus-visible,summary:focus-visible { outline:3px solid var(--accent); outline-offset:3px; }
.trace-summary { display:flex; flex-wrap:wrap; gap:10px 25px; margin:15px 0; font-size:14px; font-variant-numeric:tabular-nums; }
.chart { margin:20px 0 12px; background:#fff; border-block:1px solid var(--rule); padding:10px 8px; }
svg { display:block; width:100%; height:auto; min-height:230px; } .legend { display:flex; flex-wrap:wrap; gap:18px; font-size:13px; }
.legend span::before { content:""; display:inline-block; width:9px; height:9px; background:currentColor; border-radius:50%; margin-right:7px; }
details { border-top:1px solid var(--rule); margin-top:18px; padding-top:15px; } summary { cursor:pointer; font-size:14px; font-weight:600; }
pre { max-height:500px; overflow:auto; background:#edf0ec; padding:20px; font:12px/1.6 ui-monospace,SFMono-Regular,Consolas,monospace; white-space:pre-wrap; overflow-wrap:anywhere; }
.limitations { max-width:930px; } footer { margin-top:36px; color:var(--muted); font-size:12px; }
@media (max-width:700px) { main { padding:28px 20px 40px; } .masthead { display:block; } .scope { margin-top:12px; } h1 { margin-top:25px; } .selector { grid-template-columns:1fr; gap:14px; } th,td { padding-right:18px; } }
@media print { body { background:#fff; } main { padding:0; } section { break-inside:avoid; } .selector,details { display:none; } .table-scroll { overflow:visible; } }
@media (prefers-reduced-motion:no-preference) { select,summary { transition:background-color .15s; } select:hover,summary:hover { background-color:#e9eeea; } }
</style>
</head>
<body><main>
<header>
  <div class="masthead"><div class="brand">The Mind</div><div class="scope">__SCOPE__</div></div>
  <h1>__TITLE__</h1>
  <p class="lede">__EXPLANATION__</p>
  <p class="notes">__NOTES__</p>
</header>
<section aria-labelledby="outcomes-heading">
  <div class="section-label">01 / Condition outcomes</div>
  <h2 id="outcomes-heading">Completion on fixed deals</h2>
  <p class="caption">The primary rate includes every attempted round. The valid-only rate excludes infrastructure failures and is descriptive. Brackets show 95% Wilson intervals.</p>
  <div class="table-scroll"><table>
    <thead><tr><th scope="col">Condition and round statuses</th><th scope="col">Completed / attempted</th><th scope="col">Completion<br>all attempts</th><th scope="col">Valid rounds</th><th scope="col">Completion<br>valid only</th><th scope="col">Infrastructure<br>failure rate</th></tr></thead>
    <tbody>__CONDITIONS__</tbody>
  </table></div>
</section>
__CONTRASTS__
<section aria-labelledby="trace-heading">
  <div class="section-label">Trace explorer</div>
  <h2 id="trace-heading">Inspect a round</h2>
  <p class="caption">Recorded plays on the simulator’s virtual clock. API response latency is never plotted. Lines connect realized plays in execution order; labels identify card values.</p>
  <noscript><p>The tables above work without JavaScript. Enable JavaScript to inspect individual round traces.</p></noscript>
  <div class="selector">
    <div><label for="condition">Condition</label><select id="condition"></select></div>
    <div><label for="round">Deal seed and outcome</label><select id="round"></select></div>
  </div>
  <div id="trace-summary" class="trace-summary" aria-live="polite"></div>
  <div class="chart"><svg id="plot" viewBox="0 0 920 400" role="img" aria-labelledby="plot-title plot-description"></svg></div>
  <div id="legend" class="legend"></div>
  <p id="trace-message" class="caption"></p>
  <details><summary>Dealt hands and configuration</summary><pre id="hands"></pre></details>
  <details><summary>Raw decisions, observations, and outcomes</summary><pre id="raw"></pre></details>
</section>
<section aria-labelledby="limits-heading" class="limitations">
  <div class="section-label">Interpretation</div>
  <h2 id="limits-heading">What this pilot can establish</h2>
  <p>Timing and observed actions can convey information. Success here measures compatibility under a specified numerical protocol; it does not establish Theory of Mind, communication-free coordination, or cyber capability.</p>
  <p class="caption">A shared strictly increasing mapping from cards to play times can solve a noiseless precommitment task. Such a baseline validates mechanics; it does not demonstrate partner modeling. Small pilots should guide validation and a preregistered study, with replication across deals, models, and prompts.</p>
  <details><summary>Full experiment specification</summary><pre id="suite"></pre></details>
</section>
<footer>Standalone research artifact · all results and traces embedded · no external scripts, fonts, or services</footer>
</main>
<script type="application/json" id="report-data">__PAYLOAD__</script>
<script>
"use strict";
const data = JSON.parse(document.getElementById("report-data").textContent);
const records = data.records;
const conditionSelect = document.getElementById("condition");
const roundSelect = document.getElementById("round");
const plot = document.getElementById("plot");
const palette = ["#176c66", "#283f69", "#a9602b", "#7d527b", "#5a6c31", "#596971"];
function svgElement(tag, attrs, value) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attrs || {}).forEach(([key, item]) => element.setAttribute(key, String(item)));
  if (value !== undefined) element.textContent = String(value);
  plot.appendChild(element);
  return element;
}
function textItem(parent, value) {
  const element = document.createElement("span");
  element.textContent = value;
  parent.appendChild(element);
  return element;
}
function option(parent, value, label) {
  const element = document.createElement("option");
  element.value = value;
  element.textContent = label;
  parent.appendChild(element);
}
function draw() {
  const record = records[Number(roundSelect.value)];
  const summary = document.getElementById("trace-summary");
  const legend = document.getElementById("legend");
  summary.replaceChildren(); legend.replaceChildren(); plot.replaceChildren();
  if (!record) {
    svgElement("text", {x:460,y:190,"text-anchor":"middle",fill:"#52636b"}, "No round records available");
    return;
  }
  const plays = record.plays || [];
  const config = record.config || {};
  const hands = record.hands || [];
  textItem(summary, "Outcome: " + record.status);
  textItem(summary, "Correct prefix: " + record.correct_prefix);
  textItem(summary, "Collisions: " + record.collisions);
  textItem(summary, "Executed plays: " + plays.length);
  document.getElementById("hands").textContent = JSON.stringify({hands, config}, null, 2);
  document.getElementById("raw").textContent = JSON.stringify(record, null, 2);
  document.getElementById("trace-message").textContent = record.error
    ? "Recorded error: " + record.error
    : plays.length ? "Only executed plays are shown. Unplayed cards remain visible in the dealt hands." : "No cards were played in this round. Inspect the raw trace for its recorded outcome.";
  svgElement("title", {id:"plot-title"}, record.condition + ", seed " + record.seed + ": virtual play times");
  svgElement("desc", {id:"plot-description"}, "Horizontal axis: virtual time. Vertical axis: card value. " + plays.length + " recorded plays; outcome " + record.status + ".");
  const xMax = Math.max(1, Number(config.horizon) || 0, ...plays.map(play => Number(play.time) || 0));
  const yMax = Math.max(1, Number(config.deck_size) || 100, ...plays.map(play => Number(play.card) || 0));
  const x = time => 70 + 810 * time / xMax;
  const y = card => 330 - 290 * card / yMax;
  for (let index = 0; index <= 5; index += 1) {
    const time = xMax * index / 5;
    const card = yMax * index / 5;
    svgElement("line", {x1:70,y1:y(card),x2:880,y2:y(card),stroke:"#e2e7e4"});
    svgElement("text", {x:57,y:y(card)+4,"text-anchor":"end",fill:"#52636b","font-size":12}, +card.toFixed(1));
    svgElement("text", {x:x(time),y:354,"text-anchor":"middle",fill:"#52636b","font-size":12}, +time.toFixed(2));
  }
  svgElement("line", {x1:70,y1:330,x2:880,y2:330,stroke:"#84918f"});
  svgElement("text", {x:475,y:386,"text-anchor":"middle",fill:"#192d39","font-size":13}, "Virtual time (seconds)");
  svgElement("text", {x:70,y:20,fill:"#192d39","font-size":13}, "Card value");
  if (plays.length) {
    svgElement("polyline", {points:plays.map(play => x(play.time) + "," + y(play.card)).join(" "),fill:"none",stroke:"#adbab5","stroke-width":1.5});
    plays.forEach(play => {
      const circle = svgElement("circle", {cx:x(play.time),cy:y(play.card),r:5.5,fill:palette[play.seat % palette.length],stroke:"#fff","stroke-width":1.5});
      const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
      title.textContent = "Seat " + (play.seat + 1) + ": card " + play.card + " at virtual time " + play.time;
      circle.appendChild(title);
      svgElement("text", {x:x(play.time)+8,y:y(play.card)-8,fill:"#192d39","font-size":12}, play.card);
    });
  } else {
    svgElement("text", {x:475,y:180,"text-anchor":"middle",fill:"#52636b","font-size":16}, "No executed plays");
  }
  const seats = Math.max(hands.length, Number(config.players) || 0);
  for (let seat = 0; seat < seats; seat += 1) {
    const item = textItem(legend, "Seat " + (seat + 1));
    item.style.color = palette[seat % palette.length];
  }
}
function selectCondition() {
  const previous = records[Number(roundSelect.value)];
  roundSelect.replaceChildren();
  records.forEach((record, index) => {
    if (record.condition === conditionSelect.value) {
      option(roundSelect, String(index), "Seed " + record.seed + " · " + record.status);
      if (previous && previous.seed === record.seed) roundSelect.value = String(index);
    }
  });
  draw();
}
document.getElementById("suite").textContent = JSON.stringify(data.suite, null, 2);
[...new Set(records.map(record => record.condition))].forEach(name => option(conditionSelect, name, name));
conditionSelect.addEventListener("change", selectCondition);
roundSelect.addEventListener("change", draw);
selectCondition();
</script>
</body></html>
"""
    replacements = {
        "__TITLE__": _escape(summary["name"]),
        "__SCOPE__": _escape(scope),
        "__EXPLANATION__": _escape(explanation),
        "__NOTES__": _escape(suite.get("notes", "")),
        "__CONDITIONS__": _condition_rows(summary["conditions"]),
        "__CONTRASTS__": contrast_section,
        "__PAYLOAD__": payload,
    }
    # Replace the fixed template in one pass; user text resembling another token
    # must stay literal rather than becoming a second interpolation site.
    return re.sub(r"__[A-Z]+__", lambda match: replacements[match.group()], document)
