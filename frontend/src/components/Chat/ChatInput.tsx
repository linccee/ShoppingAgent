import { useState } from 'react';
import type { FormEvent } from 'react';

import { Button } from '../common/Button';
import styles from './ChatInput.module.css';

interface ChatInputProps {
  isStreaming: boolean;
  isStopping: boolean;
  onSubmit: (content: string) => void;
  onStop: () => void;
}

export function ChatInput({ isStreaming, isStopping, onSubmit, onStop }: ChatInputProps) {
  const [value, setValue] = useState('');

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || isStreaming) {
      return;
    }
    onSubmit(trimmed);
    setValue('');
  };

  return (
    <form className={['glass-panel', styles.form].join(' ')} onSubmit={handleSubmit}>
      <textarea
        className={styles.textarea}
        value={value}
        onChange={(event) => setValue(event.target.value)}
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
