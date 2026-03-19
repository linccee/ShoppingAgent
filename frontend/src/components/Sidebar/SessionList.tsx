import styles from './SessionList.module.css';
import type { SessionSummary } from '../../types';

interface SessionListProps {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  onSelect: (sessionId: string) => void;
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

export function SessionList({ sessions, activeSessionId, onSelect }: SessionListProps) {
  if (sessions.length === 0) {
    return <p className={styles.empty}>还没有历史会话。</p>;
  }

  return (
    <div className={styles.list}>
      {sessions.map((session) => (
        <button
          key={session.session_id}
          type="button"
          className={[
            styles.item,
            session.session_id === activeSessionId ? styles.active : '',
            'glass-panel',
          ].join(' ')}
          onClick={() => onSelect(session.session_id)}
        >
          <span className={styles.title}>{session.title}</span>
          <span className={styles.meta}>最近更新 · {formatTime(session.updated_at)}</span>
        </button>
      ))}
    </div>
  );
}
