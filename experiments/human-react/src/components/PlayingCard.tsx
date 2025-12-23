import styles from './PlayingCard.module.css';

interface PlayingCardProps {
  value: number;
}

export function PlayingCard({ value }: PlayingCardProps) {
  return (
    <div className={styles.card}>
      <span className={`${styles.corner} ${styles.top}`}>{value}</span>
      <span className={styles.value}>{value}</span>
      <span className={`${styles.corner} ${styles.bottom}`}>{value}</span>
    </div>
  );
}
