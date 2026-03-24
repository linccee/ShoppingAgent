import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  type ReactNode,
} from 'react';
import { useTranslation } from 'react-i18next';
import {
  type Language,
  type LanguagePreference,
  LANGUAGE_STORAGE_KEY,
  resolveLanguage,
} from '../i18n/constants';
import type { LanguageContextValue } from '../i18n/types';

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const { i18n } = useTranslation();

  const [preference, setPreferenceState] = useState<LanguagePreference>(() => {
    const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY);
    if (stored === 'auto' || stored === 'zh-CN' || stored === 'en-US') {
      return stored;
    }
    return 'auto';
  });

  const [isLoaded, setIsLoaded] = useState(false);

  const language = useMemo(() => resolveLanguage(preference), [preference]);

  const setPreference = useCallback(
    (newPref: LanguagePreference) => {
      setPreferenceState(newPref);
      localStorage.setItem(LANGUAGE_STORAGE_KEY, newPref);
      const resolved = resolveLanguage(newPref);
      void i18n.changeLanguage(resolved);
    },
    [i18n],
  );

  const setLanguage = useCallback(
    (lang: Language) => {
      setPreferenceState(lang);
      localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
      void i18n.changeLanguage(lang);
    },
    [i18n],
  );

  useEffect(() => {
    void i18n.changeLanguage(language);
  }, []);

  useEffect(() => {
    if (isLoaded) {
      void i18n.changeLanguage(language);
    }
  }, [language, isLoaded, i18n]);

  const syncFromBackend = useCallback(
    (backendPreference: LanguagePreference | null | undefined) => {
      if (backendPreference && backendPreference !== preference) {
        setPreferenceState(backendPreference);
        localStorage.setItem(LANGUAGE_STORAGE_KEY, backendPreference);
      }
      setIsLoaded(true);
    },
    [preference],
  );

  const value = useMemo<LanguageContextValue>(
    () => ({
      preference,
      language,
      setPreference,
      setLanguage,
      isLoaded,
      syncFromBackend,
    }),
    [preference, language, setPreference, setLanguage, isLoaded, syncFromBackend],
  );

  return (
    <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
  );
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return ctx;
}
