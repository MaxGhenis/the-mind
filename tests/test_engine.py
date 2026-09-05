import asyncio
import json
import math
import random
import unittest
from dataclasses import FrozenInstanceError, asdict

from themind.engine import Config, Decision, InvalidResponse, ProviderError, run_round


class Proportional:
    async def decide(self, observation):
        return Decision(
            tuple(card / observation.deck_size * observation.horizon for card in observation.hand)
        )


class Fixed:
    def __init__(self, times, metadata=None):
        self.times = times
        self.metadata = metadata or {}

    async def decide(self, observation):
        return Decision(self.times, self.metadata)


class Capturing(Proportional):
    def __init__(self):
        self.observations = []

    async def decide(self, observation):
        self.observations.append(observation)
        await asyncio.sleep(0)
        return await super().decide(observation)


class EngineTests(unittest.TestCase):
    def run_round(self, policies=None, **kwargs):
        config = kwargs.setdefault("config", Config(players=2))
        kwargs.setdefault("seed", 17)
        if policies is None:
            policies = [Proportional() for _ in range(config.players)]
        return asyncio.run(run_round(policies, **kwargs))

    def test_perfect_proportional_all_sizes_and_modes(self):
        for players in (2, 3, 4):
            for cards in (1, 2, 5):
                for mode in ("precommit", "feedback"):
                    with self.subTest(players=players, cards=cards, mode=mode):
                        result = self.run_round(
                            config=Config(players=players, cards_per_player=cards, mode=mode)
                        )
                        self.assertEqual(result.status, "success")
                        self.assertEqual(result.correct_prefix, players * cards)
                        self.assertEqual(
                            [p.card for p in result.plays],
                            sorted(c for h in result.hands for c in h),
                        )
                        self.assertEqual(result.collisions, 0)

    def test_own_card_inversion_is_a_game_failure(self):
        result = self.run_round([Fixed((20, 10)), Fixed((30, 40))], hands=((1, 2), (3, 4)))
        self.assertEqual(result.status, "misorder")
        self.assertEqual(result.correct_prefix, 0)
        self.assertEqual(result.plays[0].card, 2)

    def test_opponent_card_inversion_counts_correct_prefix(self):
        result = self.run_round([Fixed((1, 3)), Fixed((2, 4))], hands=((1, 2), (3, 4)))
        self.assertEqual(result.status, "misorder")
        self.assertEqual(result.correct_prefix, 1)

    def test_ties_are_card_and_seat_independent_and_atomic(self):
        first_seats = []
        for seed in range(120):
            result = self.run_round(
                [Fixed((1,)), Fixed((1,))],
                seed=seed,
                hands=((10,), (20,)),
                config=Config(players=2, cards_per_player=1),
            )
            first_seats.append(result.plays[0].seat)
            self.assertEqual(len(result.plays), 2)
            self.assertEqual(result.collisions, 1)
            swapped = self.run_round(
                [Fixed((1,)), Fixed((1,))],
                seed=seed,
                hands=((20,), (10,)),
                config=Config(players=2, cards_per_player=1),
            )
            self.assertEqual(result.plays[0].seat, swapped.plays[0].seat)
        self.assertGreater(sum(first_seats), 35)
        self.assertLess(sum(first_seats), 85)

    def test_horizon_is_inclusive_and_late_times_are_timeout(self):
        config = Config(players=2, cards_per_player=1, horizon=10)
        success = self.run_round([Fixed((1,)), Fixed((10,))], hands=((1,), (2,)), config=config)
        self.assertEqual(success.status, "success")
        late = self.run_round([Fixed((1,)), Fixed((11,))], hands=((1,), (2,)), config=config)
        self.assertEqual(late.status, "timeout")
        self.assertEqual(late.correct_prefix, 1)
        self.assertEqual(late.decisions[1].times, (11.0,))

    def test_invalid_times_and_wrong_length(self):
        for times in (
            (math.nan, 1),
            (math.inf, 1),
            (-math.inf, 1),
            (True, 1),
            (-1, 1),
            ("1", 2),
            (1,),
            None,
        ):
            with self.subTest(times=times):
                result = self.run_round([Fixed(times, {"raw": "bad output"}), Proportional()])
                self.assertEqual(result.status, "invalid_response")
                self.assertEqual(result.plays, ())
                self.assertEqual(result.decisions[0].metadata["raw"], "bad output")
                self.assertIsNone(result.decisions[0].times)
                json.dumps(asdict(result), allow_nan=False)

    def test_replay_seed_and_random_state_isolation(self):
        before = random.getstate()
        config = Config(players=3, time_quantum=10, jitter=2)
        first = self.run_round(config=config)
        second = self.run_round(config=config)
        self.assertEqual(asdict(first), asdict(second))
        self.assertEqual(before, random.getstate())
        self.assertNotEqual(first.hands, self.run_round(config=config, seed=18).hands)

    def test_observations_are_private_and_frozen(self):
        policies = [Capturing(), Capturing()]
        self.run_round(policies, hands=((2, 1), (4, 3)))
        for seat, policy in enumerate(policies):
            observation = policy.observations[0]
            self.assertEqual(observation.hand, ((1, 2), (3, 4))[seat])
            self.assertEqual(observation.history, ())
            self.assertFalse(hasattr(observation, "hands"))
            with self.assertRaises(FrozenInstanceError):
                observation.hand = (99,)

    def test_feedback_replans_from_common_snapshot(self):
        policies = [Capturing(), Capturing()]
        result = self.run_round(
            policies, hands=((1, 3), (2, 4)), config=Config(players=2, mode="feedback")
        )
        self.assertEqual(result.status, "success")
        self.assertEqual(len(policies[0].observations), 3)
        self.assertEqual(len(policies[1].observations), 4)
        for a, b in zip(policies[0].observations, policies[1].observations):
            self.assertEqual(a.now, b.now)
            self.assertEqual(a.history, b.history)
        self.assertEqual(policies[0].observations[1].hand, (3,))
        self.assertEqual([p.card for p in policies[1].observations[-1].history], [1, 2, 3])

    def test_feedback_uses_only_first_time_then_replans(self):
        class LowestOnly:
            async def decide(self, observation):
                return Decision(
                    (float(observation.hand[0]),) + (999.0,) * (len(observation.hand) - 1)
                )

        result = self.run_round(
            [LowestOnly(), LowestOnly()],
            hands=((1, 3), (2, 4)),
            config=Config(players=2, mode="feedback"),
        )
        self.assertEqual(result.status, "success")
        self.assertEqual(result.decisions[0].times, (1.0, 999.0))

    def test_feedback_ties_do_not_allow_intervening_replan(self):
        class Together:
            def __init__(self):
                self.calls = 0

            async def decide(self, observation):
                self.calls += 1
                return Decision((1.0,) * len(observation.hand))

        for seed in (1, 2, 3):
            policies = [Together(), Together()]
            result = self.run_round(
                policies,
                seed=seed,
                hands=((1,), (2,)),
                config=Config(players=2, cards_per_player=1, mode="feedback"),
            )
            self.assertEqual([p.calls for p in policies], [1, 1])
            self.assertEqual(len(result.plays), 2)
            self.assertEqual(result.collisions, 1)

    def test_cards_only_redacts_history_times_but_keeps_now(self):
        policies = [Capturing(), Capturing()]
        result = self.run_round(
            policies,
            hands=((1, 3), (2, 4)),
            config=Config(players=2, mode="feedback", feedback="cards_only"),
        )
        self.assertEqual(result.status, "success")
        observation = policies[1].observations[-1]
        self.assertEqual(observation.now, 3.0)
        self.assertTrue(all(play.time is None for play in observation.history))
        self.assertTrue(all(play.time is not None for play in result.plays))

    def test_past_time_in_feedback_is_invalid(self):
        class Past:
            async def decide(self, observation):
                return (
                    Decision((0.0,) * len(observation.hand))
                    if observation.now
                    else Decision(tuple(float(c) for c in observation.hand))
                )

        result = self.run_round(
            [Past(), Proportional()],
            hands=((1, 3), (2, 4)),
            config=Config(players=2, mode="feedback"),
        )
        self.assertEqual(result.status, "invalid_response")
        self.assertEqual(result.correct_prefix, 1)

    def test_typed_failures_are_audited_without_fallback(self):
        class Failing:
            def __init__(self, exception):
                self.exception = exception

            async def decide(self, observation):
                raise self.exception("failure", metadata={"raw": "provider evidence"})

        for exception, status in (
            (ProviderError, "provider_error"),
            (InvalidResponse, "invalid_response"),
        ):
            result = self.run_round([Failing(exception), Proportional()])
            self.assertEqual(result.status, status)
            self.assertEqual(result.plays, ())
            self.assertEqual(len(result.decisions), 2)
            self.assertIsNone(result.decisions[0].executed_times)
            self.assertEqual(result.decisions[0].metadata, {"raw": "provider evidence"})

    def test_programming_errors_propagate(self):
        class Broken:
            async def decide(self, observation):
                raise RuntimeError("bug")

        with self.assertRaisesRegex(RuntimeError, "bug"):
            self.run_round([Broken(), Proportional()])

    def test_actuation_audit_preserves_intended_times(self):
        result = self.run_round(
            [Fixed((1.1, 3.1)), Fixed((2.1, 4.1))],
            hands=((1, 3), (2, 4)),
            config=Config(players=2, time_quantum=1),
        )
        self.assertEqual(result.status, "success")
        self.assertEqual(result.decisions[0].times, (1.1, 3.1))
        self.assertEqual(result.decisions[0].executed_times, (1, 3))

    def test_config_and_hands_validation(self):
        invalid = (
            {"players": 1},
            {"players": 5},
            {"players": True},
            {"players": 2.0},
            {"cards_per_player": 0},
            {"deck_size": 1},
            {"horizon": 0},
            {"horizon": math.inf},
            {"horizon": True},
            {"jitter": -1},
            {"time_quantum": math.nan},
            {"mode": "other"},
            {"feedback": "other"},
        )
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Config(**kwargs)
        for hands in (
            ((1, 2), (2, 3)),
            ((0, 2), (3, 4)),
            ((True, 2), (3, 4)),
            ((1,), (2,)),
            ((1, 2),),
        ):
            with self.subTest(hands=hands), self.assertRaises(ValueError):
                self.run_round(hands=hands)
        with self.assertRaises(ValueError):
            self.run_round(seed=True)
        with self.assertRaises(ValueError):
            self.run_round([Proportional()])


if __name__ == "__main__":
    unittest.main()
