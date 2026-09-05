"""Deal-level summaries; never treat individual card plays as independent samples."""

import math
import random
import statistics
from collections import Counter, defaultdict

VALID_STATUSES = {"success", "misorder", "timeout"}


def wilson(successes, n):
    """95% Wilson interval, including sensible n=0 and boundary behavior."""
    if not n:
        return None
    z = 1.959963984540054
    p = successes / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return [max(0.0, center - half), min(1.0, center + half)]


def summarize(records):
    groups = defaultdict(list)
    for record in records:
        groups[record["condition"]].append(record)
    summary = {}
    for name, rows in groups.items():
        counts = Counter(row["status"] for row in rows)
        valid = sum(counts[s] for s in VALID_STATUSES)
        wins = counts["success"]
        n = len(rows)
        summary[name] = {
            "attempted": n,
            "valid": valid,
            "successes": wins,
            "status_counts": dict(counts),
            "completion_rate_all_attempts": wins / n,
            "completion_ci95_all_attempts": wilson(wins, n),
            "completion_rate_valid_only": wins / valid if valid else None,
            "completion_ci95_valid_only": wilson(wins, valid),
            "infrastructure_failure_rate": (n - valid) / n,
            "mean_correct_prefix": statistics.mean(row["correct_prefix"] for row in rows),
            "mean_collisions": statistics.mean(row["collisions"] for row in rows),
        }
    return summary


def paired_contrast(records, weights, *, bootstrap_samples=2000, seed=0):
    """Weighted condition contrast; paired resampling over identical independent deals.

    Infrastructure failures are kept in all-attempt completion but reported explicitly.
    This is descriptive pilot inference, not a substitute for preregistered power analysis.
    """
    if len(weights) < 2 or not math.isclose(sum(weights.values()), 0, abs_tol=1e-9):
        raise ValueError("Contrast needs at least two conditions and weights summing to zero")
    if bootstrap_samples < 1:
        raise ValueError("bootstrap_samples must be positive")
    paired = defaultdict(dict)
    for record in records:
        condition = record["condition"]
        if condition not in weights:
            continue
        block = record["seed"]
        if condition in paired[block]:
            raise ValueError(f"Duplicate seed/condition: {block}/{condition}")
        paired[block][condition] = record
    differences = []
    invalid_blocks = 0
    for rows in paired.values():
        if set(rows) != set(weights):
            raise ValueError("Contrast has missing condition/deal pairs")
        deals = {str(row["hands"]) for row in rows.values()}
        if len(deals) != 1:
            raise ValueError("Paired contrast requires identical hands, not merely equal seeds")
        if any(row["status"] not in VALID_STATUSES for row in rows.values()):
            invalid_blocks += 1
        differences.append(sum(w * (rows[c]["status"] == "success") for c, w in weights.items()))
    if not differences:
        raise ValueError("Contrast contains no paired deals")
    rng = random.Random(seed)
    bootstrap = sorted(
        statistics.mean(rng.choices(differences, k=len(differences)))
        for _ in range(bootstrap_samples)
    )
    return {
        "weights": weights,
        "paired_deals": len(differences),
        "blocks_with_infrastructure_failure": invalid_blocks,
        "difference_all_attempts": statistics.mean(differences),
        "paired_bootstrap_ci95": [
            bootstrap[int(0.025 * (bootstrap_samples - 1))],
            bootstrap[int(0.975 * (bootstrap_samples - 1))],
        ],
        "bootstrap_seed": seed,
        "bootstrap_samples": bootstrap_samples,
        "interpretation": "descriptive pilot; API failures confound behavioral comparisons"
        if invalid_blocks
        else "descriptive paired pilot contrast",
    }
