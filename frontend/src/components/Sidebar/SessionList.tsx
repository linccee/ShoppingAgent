import styles from './SessionList.module.css';
import type { SessionSummary } from '../../types';

interface SessionListProps {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  onSelect: (sessionId: string) => void;
  onRequestDelete: (session: SessionSummary) => void;
  isBusy: boolean;
}

function formatTime(value: string | null): string {
  if (!value) {
    return '未知时间';
  }

  return new Intl.DateTimeFormat('zh-CN', {
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
  if (sessions.length === 0) {
    return <p className={styles.empty}>还没有历史会话。</p>;
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
            <span className={styles.meta}>最近更新 · {formatTime(session.updated_at)}</span>
          </button>
          <button
            type="button"
            className={styles.deleteButton}
            aria-label={`删除会话 ${session.title}`}
            onClick={() => onRequestDelete(session)}
            disabled={isBusy}
          >
            删除
          </button>
        </article>
      ))}
    </div>
  );
}
