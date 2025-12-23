import { useState, useRef, useCallback, useEffect } from 'react';

interface UseTimerResult {
  elapsed: number;
  isRunning: boolean;
  start: () => void;
  stop: () => number;
  reset: () => void;
}

export function useTimer(maxTime: number = 30): UseTimerResult {
  const [elapsed, setElapsed] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const startTimeRef = useRef<number>(0);
  const intervalRef = useRef<number | null>(null);

  const start = useCallback(() => {
    startTimeRef.current = Date.now();
    setElapsed(0);
    setIsRunning(true);
  }, []);

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsRunning(false);
    const finalElapsed = Math.round((Date.now() - startTimeRef.current) / 100) / 10;
    return Math.min(finalElapsed, maxTime);
  }, [maxTime]);

  const reset = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setElapsed(0);
    setIsRunning(false);
  }, []);

  useEffect(() => {
    if (isRunning) {
      intervalRef.current = window.setInterval(() => {
        const currentElapsed = (Date.now() - startTimeRef.current) / 1000;
        setElapsed(currentElapsed);

        if (currentElapsed >= maxTime) {
          stop();
        }
      }, 50);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isRunning, maxTime, stop]);

  return { elapsed, isRunning, start, stop, reset };
}
