import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import styles from './Toast.module.css';

/**
 * Toast 类型枚举
 */
export type ToastType = 'success' | 'error' | 'warning' | 'info';

/**
 * Toast 位置枚举
 */
export type ToastPosition = 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';

/**
 * Toast 配置接口
 */
export interface ToastConfig {
  type: ToastType;
  message: string;
  duration?: number;
  position?: ToastPosition;
}

/**
 * Toast 项目接口
 */
interface ToastItem extends ToastConfig {
  id: string;
  exiting?: boolean;
  createdAt: number;
}

/**
 * Toast Context 接口
 */
interface ToastContextValue {
  show: (config: ToastConfig) => string;
  success: (message: string, duration?: number, position?: ToastPosition) => string;
  error: (message: string, duration?: number, position?: ToastPosition) => string;
  warning: (message: string, duration?: number, position?: ToastPosition) => string;
  info: (message: string, duration?: number, position?: ToastPosition) => string;
  remove: (id: string) => void;
}

/**
 * HMR 安全引用持有者 — 保持对 context 方法的最新引用，
 * 即使模块被热更新重载，持有者对象本身也不会被重新创建。
 */
const holder: { current: ToastContextValue | null } = { current: null };

/**
 * 默认配置
 */
const DEFAULT_DURATION = 3000;
const DEFAULT_POSITION: ToastPosition = 'top-right';
const BLINK_THRESHOLD = 2000; // 剩余 2 秒时开始闪烁

/**
 * 获取位置对应的容器样式
 */
const getContainerClass = (position: ToastPosition): string => {
  const containerClasses: Record<ToastPosition, string> = {
    'top-right': styles.toastContainerTopRight,
    'top-left': styles.toastContainerTopLeft,
    'bottom-right': styles.toastContainerBottomRight,
    'bottom-left': styles.toastContainerBottomLeft,
  };
  return `${styles.toastContainer} ${containerClasses[position]}`;
};

/**
 * 获取位置对应的滑入动画类
 */
const getSlideInClass = (position: ToastPosition): string => {
  const slideInClasses: Record<ToastPosition, string> = {
    'top-right': styles.slideInRight,
    'top-left': styles.slideInLeft,
    'bottom-right': styles.slideInBottom,
    'bottom-left': styles.slideInBottom,
  };
  return slideInClasses[position];
};

/**
 * 获取位置对应的滑出动画类
 */
const getSlideOutClass = (position: ToastPosition): string => {
  const slideOutClasses: Record<ToastPosition, string> = {
    'top-right': styles.slideOutRight,
    'top-left': styles.slideOutLeft,
    'bottom-right': styles.slideOutBottom,
    'bottom-left': styles.slideOutBottom,
  };
  return slideOutClasses[position];
};

/**
 * Toast 图标组件
 */
const ToastIcon: React.FC<{ type: ToastType }> = ({ type }) => {
  const icons: Record<ToastType, React.ReactNode> = {
    success: (
      <svg viewBox="0 0 20 20" fill="currentColor" className={styles.toastIcon}>
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
      </svg>
    ),
    error: (
      <svg viewBox="0 0 20 20" fill="currentColor" className={styles.toastIcon}>
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
      </svg>
    ),
    warning: (
      <svg viewBox="0 0 20 20" fill="currentColor" className={styles.toastIcon}>
        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
      </svg>
    ),
    info: (
      <svg viewBox="0 0 20 20" fill="currentColor" className={styles.toastIcon}>
        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
      </svg>
    ),
  };
  return <>{icons[type]}</>;
};

/**
 * 关闭图标组件
 */
const CloseIcon: React.FC = () => (
  <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
  </svg>
);

/**
 * 单个 Toast 组件
 */
const ToastItem: React.FC<{
  item: ToastItem;
  onRemove: (id: string) => void;
}> = ({ item, onRemove }) => {
  const { type, message, duration = DEFAULT_DURATION, id, exiting, position = DEFAULT_POSITION, createdAt } = item;

  const [remaining, setRemaining] = useState(duration > 0 ? duration : DEFAULT_DURATION);
  const [isBlinking, setIsBlinking] = useState(false);
  const rafRef = useRef<number>();

  // 动画帧更新剩余时间
  useEffect(() => {
    if (duration <= 0) return; // duration <= 0 表示永久显示，不启动计时器

    const startTime = Date.now();
    const initialDuration = duration;

    const tick = () => {
      const elapsed = Date.now() - startTime;
      const newRemaining = Math.max(0, initialDuration - elapsed);
      setRemaining(newRemaining);

      // 剩余 2 秒时开始闪烁
      if (newRemaining <= BLINK_THRESHOLD && newRemaining > 0) {
        setIsBlinking(true);
      }

      if (newRemaining > 0) {
        rafRef.current = requestAnimationFrame(tick);
      }
    };

    rafRef.current = requestAnimationFrame(tick);

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [duration, createdAt]);

  // 自动关闭计时器
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onRemove(id);
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, id, onRemove, createdAt]);

  const positionClass = exiting
    ? getSlideOutClass(position)
    : getSlideInClass(position);

  const typeClass = {
    success: styles.toastSuccess,
    error: styles.toastError,
    warning: styles.toastWarning,
    info: styles.toastInfo,
  }[type];

  // 进度条动画时长
  const progressDuration = duration > 0 ? `${duration}ms` : '0ms';

  return (
    <div
      className={`${styles.toast} ${typeClass} ${positionClass} ${isBlinking ? styles.toastBlinking : ''}`}
    >
      <ToastIcon type={type} />
      <span className={styles.toastMessage}>{message}</span>
      <button
        className={styles.toastClose}
        onClick={() => onRemove(id)}
        aria-label="关闭"
      >
        <CloseIcon />
      </button>
      {/* 进度条 - 永久显示的 toast 不显示进度条 */}
      {duration > 0 && (
        <div
          className={styles.progressBar}
          style={{
            width: `${(remaining / (duration > 0 ? duration : DEFAULT_DURATION)) * 100}%`,
            animationDuration: progressDuration,
            animationPlayState: exiting ? 'paused' : 'running',
          }}
        />
      )}
    </div>
  );
};

/**
 * Toast 容器组件 - 按位置分组渲染
 */
const ToastContainer: React.FC<{
  toasts: ToastItem[];
  onRemove: (id: string) => void;
}> = ({ toasts, onRemove }) => {
  if (toasts.length === 0) return null;

  // 按位置分组
  const groupedToasts: Record<ToastPosition, ToastItem[]> = {
    'top-right': [],
    'top-left': [],
    'bottom-right': [],
    'bottom-left': [],
  };

  toasts.forEach((toast) => {
    const pos = toast.position ?? DEFAULT_POSITION;
    groupedToasts[pos].push(toast);
  });

  return (
    <>
      {(Object.keys(groupedToasts) as ToastPosition[]).map((position) => {
        const positionToasts = groupedToasts[position];
        if (positionToasts.length === 0) return null;

        return (
          <div key={position} className={getContainerClass(position)}>
            {positionToasts.map((toast) => (
              <ToastItem key={toast.id} item={toast} onRemove={onRemove} />
            ))}
          </div>
        );
      })}
    </>
  );
};

/**
 * Context
 */
const ToastContext = createContext<ToastContextValue | null>(null);

/**
 * 生成唯一 ID
 */
const generateId = () => `toast-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;

/**
 * Toast Provider 组件
 */
export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const remove = useCallback((id: string) => {
    setToasts((prev) =>
      prev.map((t) => (t.id === id ? { ...t, exiting: true } : t))
    );
    // 等待动画完成后移除
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 300);
  }, []);

  const show = useCallback((config: ToastConfig): string => {
    const id = generateId();
    const newToast: ToastItem = {
      ...config,
      duration: config.duration ?? DEFAULT_DURATION,
      position: config.position ?? DEFAULT_POSITION,
      id,
      createdAt: Date.now(),
    };
    setToasts((prev) => [...prev, newToast]);
    return id;
  }, []);

  const success = useCallback((message: string, duration?: number, position?: ToastPosition) => {
    return show({ type: 'success', message, duration, position });
  }, [show]);

  const error = useCallback((message: string, duration?: number, position?: ToastPosition) => {
    return show({ type: 'error', message, duration, position });
  }, [show]);

  const warning = useCallback((message: string, duration?: number, position?: ToastPosition) => {
    return show({ type: 'warning', message, duration, position });
  }, [show]);

  const info = useCallback((message: string, duration?: number, position?: ToastPosition) => {
    return show({ type: 'info', message, duration, position });
  }, [show]);

  const contextValue = { show, success, error, warning, info, remove };

  // 每次渲染都更新持有者，让静态方法始终能访问最新引用
  holder.current = contextValue;

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <ToastContainer toasts={toasts} onRemove={remove} />
    </ToastContext.Provider>
  );
};

/**
 * Toast 工具类 - 提供类似 Python 类的调用方式
 *
 * @example
 * // 在组件中使用
 * const toast = useToast();
 * toast.success('操作成功');
 * toast.error('出错了', 5000, 'top-left');
 *
 * // 在非组件中使用
 * import { Toast } from './components/common/Toast';
 * Toast.success('消息');
 * Toast.error('错误', 3000, 'bottom-right');
 * Toast.warning('永久显示', -1); // 永久显示
 */
export class Toast {
  /**
   * 显示成功提示
   */
  static success(message: string, duration?: number, position?: ToastPosition): string {
    return holder.current?.success(message, duration, position) ?? '';
  }

  /**
   * 显示错误提示
   */
  static error(message: string, duration?: number, position?: ToastPosition): string {
    return holder.current?.error(message, duration, position) ?? '';
  }

  /**
   * 显示警告提示
   */
  static warning(message: string, duration?: number, position?: ToastPosition): string {
    return holder.current?.warning(message, duration, position) ?? '';
  }

  /**
   * 显示信息提示
   */
  static info(message: string, duration?: number, position?: ToastPosition): string {
    return holder.current?.info(message, duration, position) ?? '';
  }

  /**
   * 自定义配置显示
   */
  static show(config: ToastConfig): string {
    return holder.current?.show(config) ?? '';
  }

  /**
   * 移除指定 toast
   */
  static remove(id: string): void {
    holder.current?.remove(id);
  }
}

/**
 * useToast Hook - 在组件中使用 toast
 *
 * @example
 * const toast = useToast();
 * toast.success('保存成功');
 * toast.info('提示', 5000, 'bottom-left');
 * toast.warning('永久显示', -1); // 只能手动关闭
 */
export const useToast = (): ToastContextValue => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast 必须在 ToastProvider 内使用');
  }

  return context;
};
