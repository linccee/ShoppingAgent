/** 支持的语言类型 */
export type Language = 'zh-CN' | 'en-US' | 'ja-JP' | 'ko-KR';

/** 语言偏好值（含自动） */
export type LanguagePreference = 'auto' | Language;

/** 语言选项 */
export interface LanguageOption {
  value: LanguagePreference;
  label: string;
  nativeLabel: string;
  flag: string;
}

/** 浏览器语言到我们支持语言的映射 */
export const BROWSER_TO_LANGUAGE: Record<string, Language> = {
  'zh': 'zh-CN',
  'zh-CN': 'zh-CN',
  'zh-TW': 'zh-CN',
  'zh-HK': 'zh-CN',
  'en': 'en-US',
  'en-US': 'en-US',
  'en-GB': 'en-US',
  'ja': 'ja-JP',
  'ja-JP': 'ja-JP',
  'ko': 'ko-KR',
  'ko-KR': 'ko-KR',
};

/** 回退到英语 */
export const FALLBACK_LANGUAGE: Language = 'en-US';

/** 语言选项列表 */
export const LANGUAGE_OPTIONS: LanguageOption[] = [
  { value: 'auto', label: '自动', nativeLabel: 'Auto', flag: '🌐' },
  { value: 'zh-CN', label: '简体中文', nativeLabel: '简体中文', flag: '🇨🇳' },
  { value: 'en-US', label: 'English', nativeLabel: 'English', flag: '🇺🇸' },
  { value: 'ja-JP', label: '日本語', nativeLabel: '日本語', flag: '🇯🇵' },
  { value: 'ko-KR', label: '한국어', nativeLabel: '한국어', flag: '🇰🇷' },
];

/** localStorage key */
export const LANGUAGE_STORAGE_KEY = 'language_preference';

/** 获取浏览器的首选语言 */
export function getBrowserLanguage(): Language {
  const browserLang = navigator.language || 'en';
  return BROWSER_TO_LANGUAGE[browserLang] ?? FALLBACK_LANGUAGE;
}

/** 将 LanguagePreference 解析为实际 Language */
export function resolveLanguage(preference: LanguagePreference): Language {
  if (preference === 'auto') {
    return getBrowserLanguage();
  }
  return preference;
}
