export interface Trial {
  card: number;
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
