import { Button } from '../common/Button';
import { SessionList } from './SessionList';
import styles from './Sidebar.module.css';
import type { HealthState, Message, SessionSummary } from '../../types';

interface SidebarProps {
  sessions: SessionSummary[];
  activeSessionId: string | null;
  messages: Message[];
  inputTokens: number;
  outputTokens: number;
  health: HealthState;
  isBusy: boolean;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  onDeleteCurrent: () => void;
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
  isBusy,
  onSelectSession,
  onNewSession,
  onDeleteCurrent,
}: SidebarProps) {
  const userTurns = messages.filter((message) => message.role === 'user').length;
  const toolCalls = messages.reduce(
    (count, message) => count + (message.role === 'assistant' ? message.steps?.length ?? 0 : 0),
    0,
  );

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
        <Button variant="danger" onClick={onDeleteCurrent} disabled={isBusy || !activeSessionId}>
          清空当前对话
        </Button>
      </section>

      <section className={['glass-panel', styles.panel].join(' ')}>
        <p className="eyebrow">历史会话</p>
        <SessionList
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelect={onSelectSession}
        />
      </section>

      <section className={['glass-panel', styles.panel].join(' ')}>
        <p className="eyebrow">使用提示</p>
        <div className={styles.tipList}>
          <p><strong>预算</strong> 尽量说明预算区间，我会收敛到更可执行的方案。</p>
          <p><strong>场景</strong> 通勤、游戏、办公、拍摄等使用场景会显著影响推荐。</p>
          <p><strong>对比</strong> 可以直接让我比较两个型号或两个平台的差异。</p>
          <p><strong>切换</strong> 如果想切到全新品类，建议开启新对话。</p>
        </div>
      </section>
    </aside>
  );
}
