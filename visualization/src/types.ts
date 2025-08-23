export interface ActionData {
  action_id: number;
  player: number;
  card: number;
  decision_time: number;
  wait_time: number;
  play_time: number | null;
  llm_response_time: number | null;
  correct: boolean | null;
  error?: string;
  should_have_been?: number;
}

export interface GameData {
  game_id: string;
  timestamp: string;
  experiment: string;
  use_memory: boolean;
  temperature: number;
  num_players: number;
  round_number: number;
  success: boolean;
  cards_played: number[];
  time_taken: number;
  final_success: boolean;
  model_config: Record<string, string>;
  action_data?: ActionData[];  // New field for structured timing data
}

export interface ExperimentSummary {
  name: string;
  totalGames: number;
  successRate: number;
  avgRounds: number;
  avgTime: number;
  useMemory: boolean;
  temperature: number;
  models: string[];
}

export interface RoundVisualization {
  gameId: string;
  round: number;
  cards: CardPlay[];
  success: boolean;
  totalTime: number;
}

export interface CardPlay {
  value: number;
  player: string;
  timePlayed: number;
  correct: boolean;
}