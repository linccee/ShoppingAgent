import { useEffect, useId, useState } from 'react';

import styles from './ChatTimeline.module.css';
import type { ToolStep } from '../../types';

interface ChatTimelineProps {
  steps: ToolStep[];
  isComplete: boolean;
}

export function ChatTimeline({ steps, isComplete }: ChatTimelineProps) {
  const [isOpen, setIsOpen] = useState(!isComplete);
  const timelineId = useId();

  useEffect(() => {
    if (!isComplete) {
      setIsOpen(true);
    }
  }, [isComplete]);

  if (steps.length === 0) {
    return null;
  }

  return (
    <section className={styles.details}>
      <button
        type="button"
        className={styles.summary}
        aria-expanded={isOpen}
        aria-controls={timelineId}
        onClick={() => setIsOpen((open) => !open)}
      >
        <div className={styles.label}>
          <span>轨迹回放</span>
        </div>
        <div className={styles.controls}>
          <span className={styles.count}>{steps.length} 步</span>
          <span className={styles.toggle}>
            <span>{isOpen ? '收起' : '展开'}</span>
            <span className={styles.chevron} />
          </span>
        </div>
      </button>

      <div
        id={timelineId}
        className={[styles.collapse, isOpen ? styles.open : ''].join(' ')}
        aria-hidden={!isOpen}
      >
        <div className={styles.timelineFrame}>
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
        </div>
      </div>
    </section>
  );
}
