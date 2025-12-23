import styles from './Timer.module.css';

interface TimerProps {
  elapsed: number;
  maxTime?: number;
}

export function Timer({ elapsed, maxTime = 30 }: TimerProps) {
  const progress = Math.min(100, (elapsed / maxTime) * 100);

  return (
    <div className={styles.container}>
      <div className={styles.timer}>{elapsed.toFixed(1)}</div>
      <div className={styles.bar}>
        <div className={styles.fill} style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
}
