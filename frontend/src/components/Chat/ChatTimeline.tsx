import styles from './ChatTimeline.module.css';
import type { ToolStep } from '../../types';

interface ChatTimelineProps {
  steps: ToolStep[];
  isComplete: boolean;
}

export function ChatTimeline({ steps, isComplete }: ChatTimelineProps) {
  if (steps.length === 0) {
    return null;
  }

  return (
    <details className={styles.details} open={!isComplete}>
      <summary className={styles.summary}>
        <span>轨迹回放</span>
        <span>{steps.length} 步</span>
      </summary>

      <div className={styles.timeline}>
        {steps.map((step, index) => {
          const done = Boolean(step.output);
          return (
            <div
              key={`${step.tool}-${index}`}
              className={[
                styles.item,
                done ? styles.complete : styles.running,
              ].join(' ')}
            >
              <div className={styles.dot} aria-hidden="true" />
              <div className={['glass-panel', styles.card].join(' ')}>
                <div className={styles.header}>
                  <span className={styles.badge}>{String(index + 1).padStart(2, '0')}</span>
                  <div className={styles.meta}>
                    <span className="eyebrow">工具调用</span>
                    <strong>调用 {step.tool}</strong>
                  </div>
                  <span className={styles.status}>{done ? '已完成' : '处理中'}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </details>
  );
}
