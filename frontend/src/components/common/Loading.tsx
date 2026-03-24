import { useTranslation } from 'react-i18next';
import styles from './Loading.module.css';

interface LoadingProps {
  label?: string;
}

export function Loading({ label }: LoadingProps) {
  const { t } = useTranslation('common');
  return (
    <div className={styles.loading}>
      <span className={styles.orb} aria-hidden="true" />
      <p>{label ?? t('loading')}</p>
    </div>
  );
}
