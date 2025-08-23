# The Mind Game Data Structure

## Current Problems
The current flat CSV structure loses critical timing information:
- We only store final play order, not when each card was actually played
- We don't capture the decision process (initial wait time vs actual play time)
- We can't reconstruct the game flow or player updates
- Animation timing is fake (just dividing total time equally)

## Proposed Hierarchical Structure

### Option 1: Event-Driven (Most Detailed)
```json
{
  "game_id": "abc123",
  "experiment": "learning_gemini",
  "model_config": {"P1": "gemini-2.5-flash-lite", ...},
  "events": [
    {
      "event_type": "round_start",
      "timestamp": 0.0,
      "round_number": 1,
      "cards_dealt": {"P1": [42], "P2": [15], "P3": [78]}
    },
    {
      "event_type": "decision",
      "timestamp": 0.5,
      "player": "P1",
      "card": 42,
      "wait_time_decided": 12.5,
      "reasoning": "Medium card, wait medium time"
    },
    {
      "event_type": "decision",
      "timestamp": 0.8,
      "player": "P2", 
      "card": 15,
      "wait_time_decided": 4.5,
      "reasoning": "Low card, play soon"
    },
    {
      "event_type": "card_played",
      "timestamp": 4.5,
      "player": "P2",
      "card": 15,
      "correct": true
    },
    {
      "event_type": "update_decision",
      "timestamp": 4.6,
      "player": "P1",
      "card": 42,
      "new_wait_time": 3.0,
      "reasoning": "P2 played 15, I can play sooner now"
    },
    {
      "event_type": "card_played",
      "timestamp": 7.6,
      "player": "P1",
      "card": 42,
      "correct": true
    },
    {
      "event_type": "card_played",
      "timestamp": 12.5,
      "player": "P3",
      "card": 78,
      "correct": false,
      "should_have_been": 42
    },
    {
      "event_type": "round_failed",
      "timestamp": 12.5,
      "lives_remaining": 2
    }
  ]
}
```

### Option 2: Action-Oriented (Balanced)
```json
{
  "game_id": "abc123",
  "metadata": {
    "experiment": "learning_gemini",
    "model": "gemini-2.5-flash-lite",
    "temperature": 0.7,
    "use_memory": false
  },
  "rounds": [
    {
      "round_number": 1,
      "cards_dealt": [
        {"player": 1, "card": 42},
        {"player": 2, "card": 15},
        {"player": 3, "card": 78}
      ],
      "actions": [
        {
          "action_id": 1,
          "player": 2,
          "card": 15,
          "decision_time": 0.8,
          "wait_time": 4.5,
          "play_time": 4.5,
          "llm_response_time": 7.2,
          "correct": true
        },
        {
          "action_id": 2,
          "player": 1,
          "card": 42,
          "decision_time": 0.5,
          "wait_time": 12.5,
          "play_time": 12.5,
          "llm_response_time": 6.8,
          "correct": false,
          "error": "played_out_of_order"
        },
        {
          "action_id": 3,
          "player": 3,
          "card": 78,
          "decision_time": 1.2,
          "wait_time": 20.0,
          "play_time": null,  // Never played due to failure
          "llm_response_time": 7.5,
          "correct": null
        }
      ],
      "outcome": "failed",
      "failure_point": 12.5
    }
  ]
}
```

### Option 3: Relational Tables (SQL-friendly)

**games table:**
| game_id | experiment | model | temperature | use_memory | start_time | end_time | success |
|---------|------------|-------|-------------|------------|------------|----------|---------|
| abc123  | learning   | gemini| 0.7         | false      | ...        | ...      | false   |

**rounds table:**
| round_id | game_id | round_number | start_time | end_time | success | lives_remaining |
|----------|---------|--------------|------------|----------|---------|-----------------|
| r1       | abc123  | 1            | 0.0        | 12.5     | false   | 2               |

**cards_dealt table:**
| deal_id | round_id | player | card |
|---------|----------|--------|------|
| d1      | r1       | 1      | 42   |
| d2      | r1       | 2      | 15   |
| d3      | r1       | 3      | 78   |

**decisions table:**
| decision_id | round_id | player | card | timestamp | wait_time | llm_time | prompt | response |
|-------------|----------|--------|------|-----------|-----------|----------|--------|----------|
| dec1        | r1       | 1      | 42   | 0.5       | 12.5      | 6.8      | ...    | "12.5"   |
| dec2        | r1       | 2      | 15   | 0.8       | 4.5       | 7.2      | ...    | "4.5"    |

**plays table:**
| play_id | round_id | player | card | play_time | correct | expected_card |
|---------|----------|--------|------|-----------|---------|---------------|
| p1      | r1       | 2      | 15   | 4.5       | true    | 15            |
| p2      | r1       | 1      | 42   | 12.5      | false   | 42            |

## What We Need to Capture

1. **Initial Decisions**: When each player decides their wait time
2. **Actual Play Times**: When cards would actually be played
3. **Updates** (optional): If players can update their strategy after seeing plays
4. **LLM Performance**: Response times, prompts, reasoning
5. **Game Flow**: Exact sequence of events with timestamps
6. **Failures**: Where and why the game failed

## Benefits of Better Structure

- **Accurate Animation**: Show actual timing, not fake interpolation
- **Research Analysis**: Study coordination strategies, reaction times, learning
- **Debugging**: Understand exactly why games fail
- **Replay**: Perfect reconstruction of game flow
- **ML Training**: Rich data for training better coordination models

## Recommendation

Use **Option 2 (Action-Oriented)** for the best balance of:
- Completeness: Captures all essential timing data
- Simplicity: Easy to understand and query
- Flexibility: Can be stored as JSON or flattened to CSV
- Visualization: Maps directly to animation needs