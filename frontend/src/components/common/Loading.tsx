import styles from './Loading.module.css';

interface LoadingProps {
  label?: string;
}

export function Loading({ label = '正在准备界面...' }: LoadingProps) {
  return (
    <div className={styles.loading}>
      <span className={styles.orb} aria-hidden="true" />
      <p>{label}</p>
    </div>
  );
}
