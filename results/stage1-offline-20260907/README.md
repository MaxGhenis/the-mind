# Stage 1 offline validation, September 7, 2026

**Software controls only. No Stage 1 model data were collected.**

[Readable reports](reports/report.md) · [Validation index](validation.json) ·
[Archive verification receipt](verification.json) · [Complete evidence](evidence.tar.gz)

The frozen pilot has 5,472 requests per participant. Seven deterministic controls
produce 38,304 valid synthetic responses and pass 22 expected-signature checks.
The oracle complies on all 4,464 prescribed snapshots with zero numerical error.
The other controls distinguish unit, clock-origin, arithmetic and time-framed
polling errors, correct never-due waiting, and false activation. These values
validate software; they are not empirical findings about models.

The evidence was generated from clean source commit
`0b5d594c64177cde67e13e5367f288fdb3115021`, using the protocol with SHA-256
`96f10e44904189eee41820806aa5ab93ae532605e9e1c7650713e3185a55ac39`.
Every run includes source, exact request packets, a private canonical design,
separate original attempt/result journals, scores and reports. Source hashes are
identical across the seven runs. Interpreter identity is recorded in each manifest.

The report/summary files under `reports/` are readable copies of the sealed runs;
full verification uses the archive. The archive SHA-256 is in `evidence.sha256`.
Its contents were extracted and successfully verified with the archived source,
including raw deterministic-response replay, provenance/coverage checks and exact
report recomputation. Archived-source verification passed on Python 3.10.19,
3.12.13 and 3.14.4. See `verification.json` for the receipt.

## Verify without installing the project

Python 3.10+ and standard archive tools are sufficient. From the repository root:

```sh
cd results/stage1-offline-20260907
shasum -a 256 -c evidence.sha256
stage1_tmp=$(mktemp -d)
tar -xzf evidence.tar.gz -C "$stage1_tmp"
cd "$stage1_tmp/evidence/oracle/source"
python3 -m themind.timing_validation verify --run ../..
```

The verifier must report 38,304 control responses, all 22 checks true, and zero
model calls. It recomputes the request plan, validates every raw attempt/result
chain, checks complete coverage, replays the registered controls and regenerates
the reports. A new simulation or hosted request is not used to fill missing data.
The extracted temporary directory can be retained for inspection.

To reproduce fresh controls from the checkout:

```sh
python3 -m themind.timing_validation run \
  --protocol experiments/stage1-pilot.json --out runs/stage1-validation
python3 -m themind.timing_validation verify --run runs/stage1-validation
```

Request bytes and behavioral outcomes reproduce. Run IDs, attempt IDs, wall-clock
timestamps and measured local latency correctly change on a new run. These clocks
never advance the virtual experiment.

The full repository tests also verify invalid schemas, refusals, truncated but
parseable responses, provider errors, model mismatches, altered provenance and
partial runs. Read the [frozen protocol](../../docs/stage1-protocol.md) for definitions
and the [handoff](../../docs/stage1-handoff.md) for independent-review/network gates.
No independent reviewer approval or hosted capability result is claimed.
