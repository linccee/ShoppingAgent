import { useTranslation } from 'react-i18next';
import styles from './SessionList.module.css';
import type { SessionSummary } from '../../types';

interface SessionListProps {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  onSelect: (sessionId: string) => void;
  onRequestDelete: (session: SessionSummary) => void;
  isBusy: boolean;
}

function formatTime(value: string | null, unknownTimeLabel: string, locale: string): string {
  if (!value) {
    return unknownTimeLabel;
  }

  return new Intl.DateTimeFormat(locale, {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

export function SessionList({
  sessions,
  activeSessionId,
  onSelect,
  onRequestDelete,
  isBusy,
}: SessionListProps) {
  const { t, i18n } = useTranslation('sidebar');
  const locale = i18n.language;

  if (sessions.length === 0) {
    return <p className={styles.empty}>{t('history.empty')}</p>;
  }

  return (
    <div className={styles.list}>
      {sessions.map((session) => (
        <article
          key={session.session_id}
          className={[
            styles.item,
            session.session_id === activeSessionId ? styles.active : '',
            'glass-panel',
          ].join(' ')}
        >
          <button
            type="button"
            className={styles.content}
            onClick={() => onSelect(session.session_id)}
            disabled={isBusy}
          >
            <span className={styles.title}>{session.title}</span>
            <span className={styles.meta}>
              {t('history.lastUpdate')} · {formatTime(session.updated_at, t('history.unknownTime'), locale)}
            </span>
          </button>
          <button
            type="button"
            className={styles.deleteButton}
            aria-label={t('history.delete')}
            onClick={() => onRequestDelete(session)}
            disabled={isBusy}
          >
            {t('history.delete')}
          </button>
        </article>
      ))}
    </div>
  );
}
