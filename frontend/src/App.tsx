import { useEffect } from 'react';

import { AppProvider } from './context/AppContext';
import { useAppState } from './context/useAppStore';
import { useSessions } from './hooks/useSessions';
import { useChat } from './hooks/useChat';
import { Loading } from './components/common/Loading';
import { Sidebar } from './components/Sidebar/Sidebar';
import { Hero } from './components/Hero/Hero';
import { ChatMessage } from './components/Chat/ChatMessage';
import { ChatInput } from './components/Chat/ChatInput';
import styles from './App.module.css';

function Shell() {
  const state = useAppState();
  const { initializeApp, loadSession, createAndSelectSession, removeActiveSession } = useSessions();
  const { sendMessage, stopGeneration } = useChat();

  useEffect(() => {
    void initializeApp();
  }, [initializeApp]);

  if (state.isBootstrapping) {
    return <Loading label="正在唤醒镜澜导购..." />;
  }

  return (
    <div className={styles.shell}>
      <Sidebar
        sessions={state.sessions}
        activeSessionId={state.activeSessionId}
        messages={state.messages}
        inputTokens={state.inputTokens}
        outputTokens={state.outputTokens}
        health={state.health}
        isBusy={state.isStreaming}
        onSelectSession={(sessionId) => void loadSession(sessionId)}
        onNewSession={() => void createAndSelectSession()}
        onDeleteCurrent={() => void removeActiveSession()}
      />

      <main className={styles.main}>
        <Hero
          showPrompts={state.messages.length === 0}
          onPromptSelect={(prompt) => void sendMessage(prompt)}
        />

        {state.error ? <div className={styles.error}>{state.error}</div> : null}

        <section className={styles.conversation}>
          {state.messages.map((message, index) => (
            <ChatMessage
              key={`${message.role}-${index}`}
              message={message}
              isStreamingMessage={state.isStreaming && index === state.messages.length - 1}
            />
          ))}
        </section>

        <ChatInput
          isStreaming={state.isStreaming}
          isStopping={state.isStopping}
          onSubmit={(content) => void sendMessage(content)}
          onStop={() => void stopGeneration()}
        />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <Shell />
    </AppProvider>
  );
}
