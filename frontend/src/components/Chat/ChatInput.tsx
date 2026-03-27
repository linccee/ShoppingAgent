import { useState } from 'react';
import type { FormEvent, KeyboardEvent } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from '../common/Button';
import styles from './ChatInput.module.css';

interface ChatInputProps {
  isStreaming: boolean;
  isStopping: boolean;
  onSubmit: (content: string) => void;
  onStop: () => void;
}

export function ChatInput({ isStreaming, isStopping, onSubmit, onStop }: ChatInputProps) {
  const { t } = useTranslation('chat');
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
        <p className={styles.helperLead}>{t('input.helperLead')}</p>
        <div className={styles.helperList}>
          <div className={styles.helperItem}>
            <span className={styles.helperLabel}>{t('input.hints.budget')}</span>
            <span className={styles.helperText}>{t('input.hints.budgetText')}</span>
          </div>
          <div className={styles.helperItem}>
            <span className={styles.helperLabel}>{t('input.hints.scene')}</span>
            <span className={styles.helperText}>{t('input.hints.sceneText')}</span>
          </div>
          <div className={styles.helperItem}>
            <span className={styles.helperLabel}>{t('input.hints.compare')}</span>
            <span className={styles.helperText}>{t('input.hints.compareText')}</span>
          </div>
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
        placeholder={t('input.placeholder')}
      />
      <div className={styles.actions}>
        {isStreaming ? (
          <Button type="button" variant="danger" onClick={onStop} disabled={isStopping}>
            {isStopping ? t('input.stopping') : t('input.stop')}
          </Button>
        ) : (
          <Button type="submit" variant="primary" disabled={!value.trim()}>
            {t('input.send')}
          </Button>
        )}
      </div>
      <p className={styles.disclaimer}>{t('input.disclaimer')}</p>
    </form>
  );
}
