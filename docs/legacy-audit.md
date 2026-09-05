# Why the old findings are not a baseline

Reviewed September 5, 2026. The original local checkout is on
`feature/llm-research-paper`, committed at
`1f67edb502599af29a3f8a8fee22ff13149ba8a7`, with additional uncommitted edits.
It is preserved intact. The maintained `origin/main` was
`cf8ec352ec53dbff4cfe087cf17c1209e56d2424`; the branches have unrelated histories.
The rebuild starts from that main branch, not by overwriting the working draft.

The research branch's paper already admits that an Anthropic wrapper dropped
`response_format`, producing parsing errors and default wait times. Its model and
team comparisons therefore mix behavior with provider integration artifacts.
Its “all failed rounds were ordered correctly” observation cannot establish a
fundamental limit on numerical coordination.

Inspection of the unfinished checkout's `themind/core/game.py` also found:

- `start_round` resets the deck and reshuffles with the same seed every round;
  difficulty and dealt cards are therefore coupled rather than independently drawn.
- Every public play solicits fresh waits from all active agents and adds the
  smallest wait to the clock. This is a replanning protocol; it is not equivalent
  to simultaneously executing absolute timestamps. Absolute/delay conventions and
  timeouts cannot be interpreted without auditing each prompt version.
- The round loop checks the deadline before choosing a move, then executes a move
  even if its wait crosses the deadline.
- Exceptions produce a synthetic 10-second decision. The parser has also changed
  in the dirty checkout. No provider-family capability result is valid if errors
  silently substitute actions.
- Ties are broken by stable player-list order. Decisions for a player overwrite
  the preceding decision instead of retaining a complete action trace.
- A timeout can fail a round without losing a life; final game success uses
  `lives > 0`, so a sequence of timed-out rounds can still return game success.
- Aggregating rounds with increasing hand sizes and life-based termination mixes
  difficulty with survival. Repeated rounds are not independent observations.

These findings describe the inspected checkout; dirty changes and historical
prompt revisions mean they should not be retroactively asserted as exact causes
of every archived row. Reconstructing a historical dataset would require matching
its code, prompts, provider responses and call errors to each trial. The current
files do not justify treating the February aggregate statistics as valid evidence.

The main branch's original Streamlit files remain available as a historical demo,
outside the new benchmark package. They are not used by the new runner or tests.
The closed [research PR #1](https://github.com/MaxGhenis/the-mind/pull/1) and its
branch preserve the larger historical experiment code. Old public pages or cached
copies have not been republished or revised by this local rebuild.
