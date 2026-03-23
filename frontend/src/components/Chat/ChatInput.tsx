import { useState } from 'react';
import type { FormEvent, KeyboardEvent } from 'react';

import { Button } from '../common/Button';
import styles from './ChatInput.module.css';

const INPUT_HINTS = [
  { label: '预算', text: '说清区间更容易收敛方案' },
  { label: '场景', text: '通勤、办公、拍摄会明显改变推荐' },
  { label: '对比', text: '可以直接点名两个型号或两个平台' },
];

interface ChatInputProps {
  isStreaming: boolean;
  isStopping: boolean;
  onSubmit: (content: string) => void;
  onStop: () => void;
}

export function ChatInput({ isStreaming, isStopping, onSubmit, onStop }: ChatInputProps) {
  const [value, setValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const submitValue = () => {
    const trimmed = value.trim();
    if (!trimmed || isStreaming) {
      return;
    }
    onSubmit(trimmed);
    setValue('');
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    submitValue();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== 'Enter' || event.shiftKey || event.nativeEvent.isComposing) {
      return;
    }

    event.preventDefault();
    submitValue();
  };

  return (
    <form className={['glass-panel', styles.form].join(' ')} onSubmit={handleSubmit}>
      <div
        className={[styles.helperBar, isFocused ? '' : styles.helperBarCollapsed].join(' ')}
      >
        <p className={styles.helperLead}>把预算、场景和对比对象写清楚，答案会更快收敛到可购买结论。</p>
        <div className={styles.helperList}>
          {INPUT_HINTS.map((hint) => (
            <div key={hint.label} className={styles.helperItem}>
              <span className={styles.helperLabel}>{hint.label}</span>
              <span className={styles.helperText}>{hint.text}</span>
            </div>
          ))}
        </div>
      </div>
      <textarea
        className={styles.textarea}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        rows={1}
        placeholder="描述你的购买目标，例如：帮我挑一台预算 ¥3000 左右的降噪耳机"
      />
      <div className={styles.actions}>
        {isStreaming ? (
          <Button type="button" variant="danger" onClick={onStop} disabled={isStopping}>
            {isStopping ? '停止中...' : '停止生成'}
          </Button>
        ) : (
          <Button type="submit" variant="primary" disabled={!value.trim()}>
            发送
          </Button>
        )}
      </div>
    </form>
  );
}
