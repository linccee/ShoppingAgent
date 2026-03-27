import type { Language, LanguagePreference } from './constants';

export interface LanguageContextValue {
  /** 用户的语言偏好设置（可以是 "auto"） */
  preference: LanguagePreference;
  /** 当前激活的语言（已解析） */
  language: Language;
  /** 切换语言偏好 */
  setPreference: (pref: LanguagePreference) => void;
  /** 切换到指定语言（强制覆盖） */
  setLanguage: (lang: Language) => void;
  /** 是否已从后端加载过偏好 */
  isLoaded: boolean;
  /** 从后端同步偏好 */
  syncFromBackend: (backendPreference: LanguagePreference | null) => void;
}
