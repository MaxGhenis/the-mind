import styles from './ProgressDots.module.css';

interface ProgressDotsProps {
  total: number;
  current: number;
}

export function ProgressDots({ total, current }: ProgressDotsProps) {
  return (
    <div className={styles.progress}>
      {Array.from({ length: total }, (_, i) => (
        <div
          key={i}
          className={`${styles.dot} ${
            i < current ? styles.complete : i === current ? styles.current : ''
          }`}
        />
      ))}
    </div>
  );
}
