# The Mind: convention compatibility in LLM coordination

A small, auditable research instrument for asking when independently prompted
agents choose compatible timing conventions and how public feedback changes play.
This is a numerical scheduling variant inspired by The Mind, not the full card
game. It uses virtual time, private hands, fixed independent deals and explicit
algorithmic controls.

**Revival status:** the previous paper's findings are not validated. The rebuild
is an exploratory instrument, not evidence of theory of mind or dangerous agent
coordination. [Research design](docs/research-design.md) ·
[Legacy audit](docs/legacy-audit.md) · [Pilot status](docs/pilot.md)

The [Hugging Face investigation](https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/)
makes questions about agent coordination channels pertinent. Its agents exchanged
messages through shared infrastructure; that incident does not demonstrate
coordination without communication. Here, observable plays and timestamps are
information channels even though agents cannot chat.

## Run the instrument

Python 3.10+ is sufficient; the benchmark has **no runtime dependencies**.

```sh
python3 -m themind inspect --suite experiments/baselines.json
python3 -m themind run --suite experiments/baselines.json --out runs/baselines
```

Open `runs/baselines/report.html` to compare conditions and inspect every deal.
The report works offline and includes a virtual-time plot and raw decision traces.
Choose a new output directory for each run; existing data is never overwritten.

For an installed command and development tools:

```sh
uv venv
uv pip install --python .venv/bin/python -e '.[dev]'
.venv/bin/pytest
.venv/bin/ruff check themind tests
.venv/bin/ruff format --check themind tests
```

The original root-level Streamlit files are a historical demo and use the legacy
`requirements.txt`. They are not involved in the rebuilt benchmark.

## Model pilot

`experiments/pilot.json` defines six matched two-player, two-card deals for AA, AB,
BA, BB, explicit-convention controls, and two public-feedback variants. It names
exact economical model snapshots with native structured JSON output, verified
available on September 5, 2026; it does
not claim to use the newest or strongest models. Supply credentials through
`OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in your environment. No `.env` file is
automatically read, and credential values never belong in a suite file.

```sh
python3 -m themind inspect --suite experiments/pilot.json
python3 -m themind run --suite experiments/pilot.json \
  --out runs/pilot --allow-network --max-requests 200
```

The runner checks a worst-case API-call budget before starting. The pilot's bound
is 168 calls; actual calls depend on when feedback trials end. Token ceilings and
network timeouts are in the suite. There are no retries, hidden substitute
decisions, shared model conversations or model tools. `--max-requests` bounds
calls, not dollar cost. A one-deal integration smoke suite is provided separately.

## What is controlled

- **Precommit:** private complete schedules are frozen before the first play.
- **Feedback:** all active seats replan from the same public snapshot after each
  event. Only each seat's next lowest card is eligible.
- **Explicit convention:** a common strictly increasing card-to-time mapping
  solves the noiseless task, demonstrating why success alone is insufficient.
- **Cross-play:** AA, AB, BA and BB receive identical deals, with paired analysis.
- **Timing treatments:** quantization, bounded jitter and historical timestamp
  redaction. Redaction keeps the current event time visible.
- **Measurement:** randomized simultaneous ties; immutable private observations;
  no wall-clock latency in game outcomes; separate misorder, timeout, invalid
  response and provider-error statuses.

Feedback versus precommit also changes call budget and action constraints, so its
effect cannot be attributed solely to information. There is no cross-deal learning
yet. See the design for stronger adaptation experiments and go/no-go criteria.

## Artifacts and reproducibility

Each run writes the exact suite, an append-only `rounds.jsonl`, summaries,
`report.html`, and a manifest with artifact hashes, Python version, git state and
a source snapshot. Every request retains prompts, settings, requested and returned
model identifiers, raw responses, usage and latency. No API keys are saved.
Partial runs are marked aborted and are not presented as completed experiments.

Seeds reproduce deals, actuator randomness and tie-breaking. They do **not** make
hosted model responses deterministic. Summaries report both all-attempt and
valid-only completion with explicit denominators. Paired contrasts resample whole
deals, never individual card plays. Six-deal pilot intervals are highly uncertain
and may be degenerate; they are not grounds for a model ranking.

## Layout

| Path | Purpose |
| --- | --- |
| `themind/engine.py` | Virtual-time environment and auditable event resolution |
| `themind/policies.py` | Algorithmic policies and strict OpenAI/Anthropic HTTP adapters |
| `themind/runner.py` | Paired suites, call bounds and source manifests |
| `themind/analysis.py` | Deal-level rates and paired bootstrap contrasts |
| `themind/report.py` | Standalone report and trace viewer |
| `experiments/` | Versioned offline, smoke and exploratory pilot configurations |
| `docs/` | Research design, legacy findings and pilot interpretation |
| `results/` | Selected auditable validation runs |

Released under CC0 1.0, preserving the repository's existing license. The Mind was designed by Wolfgang Warsch; this independent research
project is not affiliated with the game's publisher.
