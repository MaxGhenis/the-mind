"""Private-hand, virtual-time coordination experiments using only the stdlib.

Policies receive immutable observations and absolute proposed play times. Wall-clock
latency never determines play order. Equal actuator times are randomly ordered;
``collisions`` counts the number of tied event groups actually encountered.
"""

from __future__ import annotations

import asyncio
import json
import math
import random
import sys
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence


def _number(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(number) or (number <= 0 if positive else number < 0):
        bound = "positive" if positive else "nonnegative"
        raise ValueError(f"{name} must be finite and {bound}")
    return number


@dataclass(frozen=True)
class Config:
    players: int = 3
    cards_per_player: int = 2
    deck_size: int = 100
    horizon: float = 100.0
    mode: str = "precommit"
    time_quantum: float = 0.0
    jitter: float = 0.0
    feedback: str = "full"

    def __post_init__(self) -> None:
        for name in ("players", "cards_per_player", "deck_size"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if not 2 <= self.players <= 4:
            raise ValueError("players must be between 2 and 4")
        if self.players * self.cards_per_player > self.deck_size:
            raise ValueError("deck_size must accommodate all dealt cards")
        _number(self.horizon, "horizon", positive=True)
        _number(self.time_quantum, "time_quantum")
        _number(self.jitter, "jitter")
        if self.mode not in ("precommit", "feedback"):
            raise ValueError("mode must be precommit or feedback")
        if self.feedback not in ("full", "cards_only"):
            raise ValueError("feedback must be full or cards_only")


@dataclass(frozen=True)
class Play:
    seat: int
    card: int
    time: float | None


@dataclass(frozen=True)
class Observation:
    seat: int
    hand: tuple[int, ...]
    now: float
    history: tuple[Play, ...]
    num_players: int
    deck_size: int
    horizon: float


@dataclass(frozen=True)
class Decision:
    times: tuple[float, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


class Policy(Protocol):
    async def decide(self, observation: Observation) -> Decision: ...


class ProviderError(Exception):
    """Expected external-provider failure, distinct from an agent decision."""

    def __init__(self, message: str, metadata: dict[str, Any] | None = None):
        super().__init__(message)
        self.metadata = metadata or {}


class InvalidResponse(Exception):
    """A provider responded, but its output cannot be used as a decision."""

    def __init__(self, message: str, metadata: dict[str, Any] | None = None):
        super().__init__(message)
        self.metadata = metadata or {}


@dataclass(frozen=True)
class DecisionRecord:
    observation: Observation
    times: tuple[float, ...] | None
    metadata: dict[str, Any]
    executed_times: tuple[float, ...] | None
    error: str | None = None


@dataclass(frozen=True)
class Result:
    seed: int
    config: Config
    hands: tuple[tuple[int, ...], ...]
    status: str
    plays: tuple[Play, ...]
    decisions: tuple[DecisionRecord, ...]
    collisions: int
    correct_prefix: int
    error: str | None = None


def _metadata(value: Any) -> dict[str, Any]:
    """Preserve failure evidence while keeping the result JSON serializable."""
    try:
        if not isinstance(value, dict):
            raise TypeError("metadata must be a dictionary")
        json.dumps(value, allow_nan=False)
        return deepcopy(value)
    except (TypeError, ValueError, OverflowError, RecursionError):
        return {"unserializable_metadata": repr(value)}


def _validate(decision: Any, observation: Observation) -> tuple[float, ...]:
    if not isinstance(decision, Decision):
        raise InvalidResponse("policy must return a Decision")
    metadata = _metadata(decision.metadata)
    if not isinstance(decision.times, (tuple, list)):
        raise InvalidResponse("times must be a sequence", metadata)
    if len(decision.times) != len(observation.hand):
        raise InvalidResponse("one time is required for each card in hand", metadata)
    times = []
    for value in decision.times:
        try:
            number = _number(value, "decision time")
        except ValueError as exc:
            raise InvalidResponse(str(exc), metadata) from exc
        if number < observation.now:
            raise InvalidResponse("decision times must be at least now", metadata)
        times.append(number)
    return tuple(times)


def _actuate(time: float, now: float, config: Config, rng: random.Random) -> float:
    if config.jitter:
        # Multiplication avoids the overflow of uniform(-jitter, jitter)'s span.
        time += (2 * rng.random() - 1) * config.jitter
    time = max(now, min(sys.float_info.max, time))
    if config.time_quantum:
        units = time / config.time_quantum
        if math.isfinite(units):
            # Round half upward, rather than Python's round-to-even convention.
            time = min(sys.float_info.max, math.floor(units + 0.5) * config.time_quantum)
    return max(now, time)


def _hands(config: Config, seed: int, hands: Sequence[Sequence[int]] | None):
    if hands is None:
        deck = random.Random(f"the-mind:{seed}:deal").sample(
            range(1, config.deck_size + 1), config.players * config.cards_per_player
        )
        hands = tuple(
            deck[seat * config.cards_per_player : (seat + 1) * config.cards_per_player]
            for seat in range(config.players)
        )
    if len(hands) != config.players:
        raise ValueError("hands must contain one hand per player")
    result = []
    seen = set()
    for hand in hands:
        if len(hand) != config.cards_per_player:
            raise ValueError("each hand must contain cards_per_player cards")
        for card in hand:
            if type(card) is not int or not 1 <= card <= config.deck_size:
                raise ValueError("cards must be integers from 1 through deck_size")
            if card in seen:
                raise ValueError("dealt cards must be unique")
            seen.add(card)
        result.append(tuple(sorted(hand)))
    return tuple(result)


async def run_round(
    policies: Sequence[Policy],
    *,
    seed: int,
    config: Config | None = None,
    hands: Sequence[Sequence[int]] | None = None,
) -> Result:
    """Run one round, terminating at a misorder, timeout, or typed failure.

    Precommit freezes one schedule per seat. Feedback replans all active seats
    from one common event snapshot, using only each lowest card's proposed time.
    Tied plays execute as a batch before replanning. A card at exactly ``horizon``
    is on time. Jitter is uniform +/- ``jitter``, followed by nearest-quantum
    rounding (halves upward) and clamping to the current virtual time.

    All providers in an event are awaited and audited. If multiple typed failures
    occur together, the first by seat determines the round status. Unexpected
    exceptions propagate. No failed response is replaced with a fallback policy.
    """
    policies = tuple(policies)
    config = config if config is not None else Config(players=len(policies))
    if not isinstance(config, Config):
        raise ValueError("config must be a Config")
    if len(policies) != config.players:
        raise ValueError("policies must contain one policy per player")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    dealt = _hands(config, seed, hands)
    remaining = [list(hand) for hand in dealt]
    expected = sorted(card for hand in dealt for card in hand)
    plays: list[Play] = []
    records: list[DecisionRecord] = []
    collision_rng = random.Random(f"the-mind:{seed}:ties")
    actuator_rng = [random.Random(f"the-mind:{seed}:actuator:{s}") for s in range(config.players)]
    collisions = 0
    prefix = 0
    now = 0.0

    def finish(status: str, error: str | None = None) -> Result:
        return Result(
            seed, config, dealt, status, tuple(plays), tuple(records), collisions, prefix, error
        )

    async def decide(seat: int, history: tuple[Play, ...]):
        observation = Observation(
            seat,
            tuple(remaining[seat]),
            now,
            history,
            config.players,
            config.deck_size,
            config.horizon,
        )
        try:
            decision = await policies[seat].decide(observation)
            times = _validate(decision, observation)
        except (ProviderError, InvalidResponse) as exc:
            status = "provider_error" if isinstance(exc, ProviderError) else "invalid_response"
            record = DecisionRecord(observation, None, _metadata(exc.metadata), None, str(exc))
            return record, status
        executed = tuple(_actuate(t, now, config, actuator_rng[seat]) for t in times)
        return DecisionRecord(observation, times, _metadata(decision.metadata), executed), None

    scheduled: list[Play] = []
    while prefix < len(expected):
        if config.mode == "feedback" or not records:
            history = tuple(plays)
            if config.feedback == "cards_only":
                history = tuple(Play(p.seat, p.card, None) for p in plays)
            active = [seat for seat, hand in enumerate(remaining) if hand]
            # Every observation is prepared from unchanged state before any play.
            outcomes = await asyncio.gather(*(decide(seat, history) for seat in active))
            records.extend(record for record, _ in outcomes)
            for record, status in outcomes:
                if status is not None:
                    return finish(status, f"seat {record.observation.seat}: {record.error}")
            scheduled = []
            for record, _ in outcomes:
                seat = record.observation.seat
                assert record.executed_times is not None
                events = [
                    Play(seat, card, t) for card, t in zip(remaining[seat], record.executed_times)
                ]
                scheduled.extend(events[:1] if config.mode == "feedback" else events)
        next_time = min(p.time for p in scheduled)
        assert next_time is not None
        if next_time > config.horizon:
            return finish("timeout", "next scheduled play exceeds horizon")
        now = next_time
        batch = [play for play in scheduled if play.time == next_time]
        scheduled = [play for play in scheduled if play.time != next_time]
        if len(batch) > 1:
            collisions += 1
            collision_rng.shuffle(batch)
        # A tied batch is observed atomically, including when its ordering fails.
        plays.extend(batch)
        for play in batch:
            remaining[play.seat].remove(play.card)
        for play in batch:
            if play.card != expected[prefix]:
                return finish("misorder", f"played {play.card} before {expected[prefix]}")
            prefix += 1
    return finish("success")
