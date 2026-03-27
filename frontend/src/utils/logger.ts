/**
 * Frontend logging utility with localStorage persistence and optional backend sync.
 * Log levels: debug, info, warn, error
 */

export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
}

const LOG_PREFIX = '[FRONTEND]';
const STORAGE_KEY = 'app_logs';

// Maximum logs to keep in localStorage
const MAX_STORED_LOGS = 100;

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: string;
  data?: unknown;
}

function formatTimestamp(): string {
  const now = new Date();
  return now.toISOString();
}

function shouldLog(level: LogLevel): boolean {
  // In production, only log WARN and ERROR
  if (import.meta.env.PROD) {
    return level === LogLevel.WARN || level === LogLevel.ERROR;
  }
  return true;
}

function storeLog(entry: LogEntry): void {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    const logs: LogEntry[] = stored ? JSON.parse(stored) : [];
    logs.push(entry);
    // Keep only the most recent logs
    if (logs.length > MAX_STORED_LOGS) {
      logs.splice(0, logs.length - MAX_STORED_LOGS);
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(logs));
  } catch {
    // Ignore storage errors
  }
}

function createLogEntry(
  level: LogLevel,
  message: string,
  context?: string,
  data?: unknown,
): LogEntry {
  return {
    timestamp: formatTimestamp(),
    level,
    message,
    context,
    data,
  };
}

function log(level: LogLevel, message: string, context?: string, data?: unknown): void {
  if (!shouldLog(level)) return;

  const entry = createLogEntry(level, message, context, data);
  const prefix = context ? `${LOG_PREFIX} [${context}]` : LOG_PREFIX;

  const logMethods: Record<LogLevel, (message: string, ...args: unknown[]) => void> = {
    [LogLevel.DEBUG]: console.debug,
    [LogLevel.INFO]: console.info,
    [LogLevel.WARN]: console.warn,
    [LogLevel.ERROR]: console.error,
  };

  const method = logMethods[level];
  if (data) {
    method(`${prefix} ${message}`, data);
  } else {
    method(`${prefix} ${message}`);
  }

  // Store in localStorage for persistence
  storeLog(entry);
}

export const logger = {
  debug(message: string, context?: string, data?: unknown): void {
    log(LogLevel.DEBUG, message, context, data);
  },

  info(message: string, context?: string, data?: unknown): void {
    log(LogLevel.INFO, message, context, data);
  },

  warn(message: string, context?: string, data?: unknown): void {
    log(LogLevel.WARN, message, context, data);
  },

  error(message: string, context?: string, data?: unknown): void {
    log(LogLevel.ERROR, message, context, data);
  },

  getStoredLogs(): LogEntry[] {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  },

  clearLogs(): void {
    localStorage.removeItem(STORAGE_KEY);
  },
};
