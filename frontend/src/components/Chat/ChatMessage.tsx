import { useTranslation } from 'react-i18next';
import { ChatTimeline } from './ChatTimeline';
import { MarkdownContent } from './MarkdownContent';
import styles from './ChatMessage.module.css';
import type { Message } from '../../types';

interface ChatMessageProps {
  message: Message;
  isStreamingMessage: boolean;
}

export function ChatMessage({ message, isStreamingMessage }: ChatMessageProps) {
  const { t } = useTranslation('chat');
  const isAssistant = message.role === 'assistant';
  const content = message.content || (isStreamingMessage ? t('message.thinking') : '');

  return (
    <article
      className={[
        styles.message,
        isAssistant ? styles.assistant : styles.user,
      ].join(' ')}
    >
      <div className={styles.avatar}>{isAssistant ? '🪞' : '🧑'}</div>
      <div className={['glass-panel', styles.body].join(' ')}>
        {isAssistant && message.steps?.length ? (
          <ChatTimeline steps={message.steps} isComplete={!isStreamingMessage} />
        ) : null}
        <div className={styles.content}>
          {isAssistant ? <MarkdownContent content={content} /> : content}
        </div>
      </div>
    </article>
  );
}
