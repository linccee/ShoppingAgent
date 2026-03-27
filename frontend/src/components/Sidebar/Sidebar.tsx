import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { Button } from '../common/Button';
import { ConfirmDialog } from '../common/ConfirmDialog';
import { Toast } from '../common/Toast';
import { SessionList } from './SessionList';
import { useAuth } from '../../context/AuthContext';
import styles from './Sidebar.module.css';
import type { HealthState, Message, RuntimeConfig, SessionSummary } from '../../types';

interface SidebarProps {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  messages: Message[];
  inputTokens: number;
  outputTokens: number;
  health: HealthState;
  runtimeConfig: RuntimeConfig;
  isBusy: boolean;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  onDeleteCurrent: () => void;
  onDeleteSession: (sessionId: string) => Promise<void>;
}

export function Sidebar({
  sessions,
  activeSessionId,
  messages,
  inputTokens,
  outputTokens,
  health,
  runtimeConfig,
  isBusy,
  onSelectSession,
  onNewSession,
  onDeleteCurrent,
  onDeleteSession,
}: SidebarProps) {
  const { t } = useTranslation('sidebar');
  const { user, logout } = useAuth();
  const [pendingDelete, setPendingDelete] = useState<SessionSummary | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const userTurns = messages.filter((message) => message.role === 'user').length;
  const toolCalls = messages.reduce(
    (count, message) => count + (message.role === 'assistant' ? message.steps?.length ?? 0 : 0),
    0,
  );
  const activeSession = sessions.find((session) => session.session_id === activeSessionId) ?? null;

  async function confirmDeleteSession(): Promise<void> {
    if (!pendingDelete) {
      return;
    }

    setIsDeleting(true);
    setDeleteError(null);

    try {
      await onDeleteSession(pendingDelete.session_id);
      setPendingDelete(null);
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : t('confirmDelete.failed'));
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <aside className={styles.sidebar}>
      <section className={['glass-panel', styles.brand].join(' ')}>
        <p className="eyebrow">Mirror Curation</p>
        <div className={styles.titleRow}>
          <span className={styles.logo}>◌</span>
          <div>
            <h1>{t('brand.title')}</h1>
            <p>{t('brand.tagline')}</p>
          </div>
        </div>
        <div className="status-badge">
          <span className={styles.statusDot} />
          {t(`health.${health === 'ok' ? 'ok' : health === 'degraded' ? 'degraded' : health === 'error' ? 'error' : 'loading'}`)}
        </div>
      </section>

      <section className={['glass-panel', styles.panel].join(' ')}>
        <div className={styles.userSection}>
          <div className={styles.userAvatar}>
            {user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className={styles.userInfo}>
            <span className={styles.userName}>{user?.username}</span>
            <Link to="/profile" className={styles.profileLink}>{t('userSection.settings')}</Link>
          </div>
          <button
            type="button"
            onClick={() => {
              Toast.info(t('userSection.logoutToast'), 3000);
              logout();
            }}
            className={styles.logoutBtn}
            title={t('userSection.logout')}
            aria-label={t('userSection.logout')}
          >
            {t('userSection.logout')}
          </button>
        </div>
      </section>

      <section className={['glass-panel', styles.panel].join(' ')}>
        <p className="eyebrow">{t('config.title')}</p>
        <div className={styles.metricRow}>
          <span>{t('config.model')}</span>
          <strong className={styles.metricValue}>{runtimeConfig.model ?? t('config.notSet')}</strong>
        </div>
        <div className={styles.metricRow}>
          <span>{t('config.temperature')}</span>
          <strong>{runtimeConfig.temperature}</strong>
        </div>
        <div className={styles.metricRow}>
          <span>{t('config.maxTokens')}</span>
          <strong>{runtimeConfig.max_tokens}</strong>
        </div>
        <div className={styles.metricRow}>
          <span>{t('config.memoryTurns')}</span>
          <strong>{runtimeConfig.memory_turns} {t('config.turnsUnit')}</strong>
        </div>
      </section>

      <section className={['glass-panel', styles.panel].join(' ')}>
        <p className="eyebrow">{t('overview.title')}</p>
        <div className={styles.metricRow}>
          <span>{t('overview.questionCount')}</span>
          <strong>{userTurns}</strong>
        </div>
        <div className={styles.metricRow}>
          <span>{t('overview.toolCalls')}</span>
          <strong>{toolCalls}</strong>
        </div>
        <div className={styles.metricRow}>
          <span>{t('overview.inputTokens')}</span>
          <strong>{inputTokens}</strong>
        </div>
        <div className={styles.metricRow}>
          <span>{t('overview.outputTokens')}</span>
          <strong>{outputTokens}</strong>
        </div>
      </section>

      <section className={styles.actions}>
        <Button variant="primary" onClick={onNewSession} disabled={isBusy}>
          {t('actions.newSession')}
        </Button>
        <Button
          variant="danger"
          onClick={() => {
            if (activeSession) {
              setDeleteError(null);
              setPendingDelete(activeSession);
              return;
            }
            onDeleteCurrent();
          }}
          disabled={isBusy || !activeSessionId}
        >
          {t('actions.clearCurrent')}
        </Button>
      </section>

      <section className={['glass-panel', styles.panel].join(' ')}>
        <p className="eyebrow">{t('history.title')}</p>
        <SessionList
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelect={onSelectSession}
          onRequestDelete={(session) => {
            setDeleteError(null);
            setPendingDelete(session);
          }}
          isBusy={isBusy || isDeleting}
        />
      </section>

      {pendingDelete ? (
        <ConfirmDialog
          title={t('confirmDelete.title', { title: pendingDelete.title })}
          description={t('confirmDelete.description')}
          confirmLabel={t('confirmDelete.confirm')}
          isProcessing={isDeleting}
          error={deleteError}
          onCancel={() => {
            if (isDeleting) {
              return;
            }
            setDeleteError(null);
            setPendingDelete(null);
          }}
          onConfirm={() => {
            void confirmDeleteSession();
          }}
        />
      ) : null}
    </aside>
  );
}
