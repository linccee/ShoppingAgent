import { useState } from 'react';

import { Button } from '../common/Button';
import { ConfirmDialog } from '../common/ConfirmDialog';
import { SessionList } from './SessionList';
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

function getHealthLabel(health: HealthState): string {
  switch (health) {
    case 'ok':
      return '后端在线';
    case 'degraded':
      return '服务降级';
    case 'error':
      return '服务不可达';
    default:
      return '检测中';
  }
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
      setDeleteError(error instanceof Error ? error.message : '删除会话失败');
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
            <h1>镜澜导购</h1>
            <p>把价格、评论与购买判断，整理成更清晰的结论。</p>
          </div>
        </div>
        <div className="status-badge">
          <span className={styles.statusDot} />
          {getHealthLabel(health)}
        </div>
      </section>

      <section className={['glass-panel', styles.panel].join(' ')}>
        <p className="eyebrow">当前配置</p>
        <div className={styles.metricRow}>
          <span>模型</span>
          <strong className={styles.metricValue}>{runtimeConfig.model ?? '未设置'}</strong>
        </div>
        <div className={styles.metricRow}>
          <span>温度</span>
          <strong>{runtimeConfig.temperature}</strong>
        </div>
        <div className={styles.metricRow}>
          <span>Max Tokens</span>
          <strong>{runtimeConfig.max_tokens}</strong>
        </div>
        <div className={styles.metricRow}>
          <span>记忆轮次</span>
          <strong>{runtimeConfig.memory_turns} 轮</strong>
        </div>
      </section>

      <section className={['glass-panel', styles.panel].join(' ')}>
        <p className="eyebrow">本轮概览</p>
        <div className={styles.metricRow}>
          <span>提问次数</span>
          <strong>{userTurns}</strong>
        </div>
        <div className={styles.metricRow}>
          <span>工具调用</span>
          <strong>{toolCalls}</strong>
        </div>
        <div className={styles.metricRow}>
          <span>输入 Token</span>
          <strong>{inputTokens}</strong>
        </div>
        <div className={styles.metricRow}>
          <span>输出 Token</span>
          <strong>{outputTokens}</strong>
        </div>
      </section>

      <section className={styles.actions}>
        <Button variant="primary" onClick={onNewSession} disabled={isBusy}>
          开启新对话
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
          清空当前对话
        </Button>
      </section>

      <section className={['glass-panel', styles.panel].join(' ')}>
        <p className="eyebrow">历史会话</p>
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
          title={`删除「${pendingDelete.title}」？`}
          description="确认后会同时删除数据库记录、内存中的会话列表缓存，以及浏览器里保存的当前会话标识。这个操作无法撤销。"
          confirmLabel="确认删除"
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
