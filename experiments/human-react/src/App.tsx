import { useState, useEffect, useCallback, useRef } from 'react';
import './App.css';
import type { Trial, Phase } from './types';
import { PlayingCard } from './components/PlayingCard';
import { ProgressDots } from './components/ProgressDots';
import { Timer } from './components/Timer';
import { useTimer } from './hooks/useTimer';

const TOTAL_TRIALS = 10;
const MAX_TIME = 30;

function generateCards(): number[] {
  const ranges: [number, number][] = [
    [1, 15], [10, 25], [20, 40], [35, 55], [45, 65],
    [55, 75], [65, 85], [75, 90], [85, 100], [90, 100]
  ];
  const cards = ranges.map(([min, max]) =>
    Math.floor(Math.random() * (max - min + 1)) + min
  );
  return cards.sort(() => Math.random() - 0.5);
}

function App() {
  const [phase, setPhase] = useState<Phase>('intro');
  const [trials, setTrials] = useState<Trial[]>([]);
  const [currentTrial, setCurrentTrial] = useState(0);
  const [predictionValue, setPredictionValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const { elapsed, isRunning, start: startTimer, stop: stopTimer, reset: resetTimer } = useTimer(MAX_TIME);

  const startExperiment = useCallback(() => {
    const cards = generateCards();
    setTrials(cards.map(card => ({ card, predicted: null, actual: null })));
    setCurrentTrial(0);
    setPhase('prediction');
    setPredictionValue('');
  }, []);

  const submitPrediction = useCallback(() => {
    const val = parseFloat(predictionValue) || 0;
    const clampedVal = Math.max(0, Math.min(30, val));

    setTrials(prev => prev.map((t, i) =>
      i === currentTrial ? { ...t, predicted: clampedVal } : t
    ));

    setPhase('reactive');
    resetTimer();
    startTimer();
  }, [predictionValue, currentTrial, resetTimer, startTimer]);

  const playCard = useCallback(() => {
    const actualTime = stopTimer();

    setTrials(prev => prev.map((t, i) =>
      i === currentTrial ? { ...t, actual: actualTime } : t
    ));

    setTimeout(() => {
      if (currentTrial < TOTAL_TRIALS - 1) {
        setCurrentTrial(prev => prev + 1);
        setPhase('prediction');
        setPredictionValue('');
      } else {
        setPhase('results');
      }
    }, 400);
  }, [currentTrial, stopTimer]);

  // Auto-play when timer reaches max
  useEffect(() => {
    if (isRunning && elapsed >= MAX_TIME) {
      playCard();
    }
  }, [elapsed, isRunning, playCard]);

  // Focus input when prediction phase starts
  useEffect(() => {
    if (phase === 'prediction' && inputRef.current) {
      inputRef.current.focus();
    }
  }, [phase, currentTrial]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && phase === 'prediction') {
        submitPrediction();
      }
      if (e.key === ' ' && phase === 'reactive') {
        e.preventDefault();
        playCard();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [phase, submitPrediction, playCard]);

  const calculateResults = useCallback(() => {
    let consistent = 0;
    let totalGap = 0;
    let totalBias = 0;

    for (const t of trials) {
      if (t.predicted !== null && t.actual !== null) {
        const gap = Math.abs(t.predicted - t.actual);
        const bias = t.predicted - t.actual;
        if (gap <= 2) consistent++;
        totalGap += gap;
        totalBias += bias;
      }
    }

    return {
      consistency: Math.round(100 * consistent / TOTAL_TRIALS),
      avgGap: (totalGap / TOTAL_TRIALS).toFixed(1),
      avgBias: totalBias / TOTAL_TRIALS
    };
  }, [trials]);

  const copyData = useCallback(() => {
    const data = {
      timestamp: new Date().toISOString(),
      trials,
      summary: {
        consistency: trials.filter(t =>
          t.predicted !== null && t.actual !== null &&
          Math.abs(t.predicted - t.actual) <= 2
        ).length / TOTAL_TRIALS,
        avgGap: trials.reduce((s, t) =>
          s + (t.predicted !== null && t.actual !== null ? Math.abs(t.predicted - t.actual) : 0), 0
        ) / TOTAL_TRIALS,
        avgBias: trials.reduce((s, t) =>
          s + (t.predicted !== null && t.actual !== null ? t.predicted - t.actual : 0), 0
        ) / TOTAL_TRIALS
      }
    };
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    alert('Copied to clipboard!');
  }, [trials]);

  const restart = useCallback(() => {
    setPhase('intro');
    setTrials([]);
    setCurrentTrial(0);
    setPredictionValue('');
    resetTimer();
  }, [resetTimer]);

  if (phase === 'intro') {
    return (
      <div className="container">
        <h1>The <span className="highlight">Mind</span></h1>
        <div className="subtitle">Human Timing Experiment</div>

        <div className="experimentCard">
          <div className="instructions">
            <p><strong>The Mind</strong> is a card game where players play cards 1-100 in order, using only their sense of timing.</p>
            <br />
            <p>You'll see a card and do two things:</p>
            <br />
            <p><strong>1. Predict</strong> - How long would you wait?</p>
            <p><strong>2. React</strong> - Watch time pass. Click when ready.</p>
            <br />
            <p>We measure if your prediction matches your action.</p>
          </div>

          <button onClick={startExperiment}>Begin Experiment</button>

          <p style={{ marginTop: '2rem', fontSize: '0.7rem', color: 'var(--muted)' }}>
            10 trials · ~3 minutes · keyboard: Enter, Space
          </p>
        </div>
      </div>
    );
  }

  if (phase === 'prediction') {
    const currentCard = trials[currentTrial]?.card ?? 0;

    return (
      <div className="container">
        <div className="phase">Phase 1 - Predict</div>
        <ProgressDots total={TOTAL_TRIALS} current={currentTrial} />

        <div className="experimentCard">
          <PlayingCard value={currentCard} />

          <div className="instructions" style={{ marginBottom: '1rem' }}>
            No cards played yet. How many seconds would you wait?
          </div>

          <div className="inputGroup">
            <input
              ref={inputRef}
              type="number"
              min="0"
              max="30"
              step="0.5"
              placeholder="0"
              value={predictionValue}
              onChange={(e) => setPredictionValue(e.target.value)}
            />
            <span className="inputSuffix">seconds</span>
          </div>

          <button onClick={submitPrediction}>Submit → Start Timer</button>
        </div>
      </div>
    );
  }

  if (phase === 'reactive') {
    const currentCard = trials[currentTrial]?.card ?? 0;

    return (
      <div className="container">
        <div className="phase">Phase 2 - React</div>
        <ProgressDots total={TOTAL_TRIALS} current={currentTrial} />

        <div className="experimentCard">
          <PlayingCard value={currentCard} />
          <Timer elapsed={elapsed} maxTime={MAX_TIME} />
          <button className="btnPlay" onClick={playCard}>
            Play Card
          </button>
        </div>
      </div>
    );
  }

  if (phase === 'results') {
    const results = calculateResults();

    return (
      <div className="container">
        <h1>Your <span className="highlight">Results</span></h1>
        <div className="subtitle">Prediction vs Reaction</div>

        <div className="experimentCard">
          <div className="resultsGrid">
            <div className="stat">
              <div className="statValue">{results.consistency}%</div>
              <div className="statLabel">Consistency</div>
            </div>
            <div className="stat">
              <div className="statValue">{results.avgGap}s</div>
              <div className="statLabel">Avg Gap</div>
            </div>
            <div className="stat">
              <div className="statValue">
                {results.avgBias >= 0 ? '+' : ''}{results.avgBias.toFixed(1)}s
              </div>
              <div className="statLabel">Bias</div>
            </div>
          </div>

          <table className="resultsTable">
            <thead>
              <tr>
                <th>Card</th>
                <th>Predicted</th>
                <th>Actual</th>
                <th>Gap</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {trials.map((t, i) => {
                if (t.predicted === null || t.actual === null) return null;
                const gap = Math.abs(t.predicted - t.actual);
                const isMatch = gap <= 2;
                return (
                  <tr key={i}>
                    <td>{t.card}</td>
                    <td>{t.predicted.toFixed(1)}s</td>
                    <td>{t.actual.toFixed(1)}s</td>
                    <td>{gap.toFixed(1)}s</td>
                    <td className={isMatch ? 'match' : 'noMatch'}>
                      {isMatch ? '✓' : '✗'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <div className="compareBox">
            <h4>LLM Comparison</h4>
            <p>
              GPT-4o-mini showed <strong>20% consistency</strong> with a tendency to
              <strong> over-predict</strong> wait times - saying it would wait longer
              than it actually did when asked moment-by-moment.
            </p>
          </div>

          <div className="btnGroup">
            <button className="btnSecondary" onClick={copyData}>Copy JSON</button>
            <button onClick={restart}>Run Again</button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

export default App;
