export interface Trial {
  card: number;
  players: number;  // total players including you (2-4)
  predicted: number | null;
  actual: number | null;
}

export type Phase = 'intro' | 'prediction' | 'reactive' | 'results';

export interface ExperimentState {
  phase: Phase;
  trials: Trial[];
  currentTrial: number;
}

export interface ResultsSummary {
  consistency: number;
  avgGap: number;
  avgBias: number;
}
