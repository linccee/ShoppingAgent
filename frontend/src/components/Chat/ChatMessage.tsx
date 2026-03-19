import { ChatTimeline } from './ChatTimeline';
import styles from './ChatMessage.module.css';
import type { Message } from '../../types';

interface ChatMessageProps {
  message: Message;
  isStreamingMessage: boolean;
}

export function ChatMessage({ message, isStreamingMessage }: ChatMessageProps) {
  const isAssistant = message.role === 'assistant';

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
        <div className={styles.content}>{message.content || (isStreamingMessage ? '思考中...' : '')}</div>
      </div>
    </article>
  );
}
