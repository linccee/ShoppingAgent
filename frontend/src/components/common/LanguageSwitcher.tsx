import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useLanguage } from '../../context/LanguageContext';
import { LANGUAGE_OPTIONS, resolveLanguage, type LanguagePreference } from '../../i18n/constants';
import styles from './LanguageSwitcher.module.css';

export function LanguageSwitcher() {
  const { t } = useTranslation('common');
  const { preference, setPreference } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const currentOption = LANGUAGE_OPTIONS.find((o) => o.value === preference) ?? LANGUAGE_OPTIONS[0];
  const autoResolved = resolveLanguage('auto');

  const handleSelect = (value: LanguagePreference) => {
    setPreference(value);
    setIsOpen(false);
  };

  return (
    <div className={styles.wrapper} ref={ref}>
      <button
        type="button"
        className={styles.trigger}
        onClick={() => setIsOpen((o) => !o)}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        title={t('languageSwitcher.title')}
      >
        <span className={styles.flag}>{currentOption.flag}</span>
        <span className={styles.label}>{currentOption.nativeLabel}</span>
        <span className={[styles.chevron, isOpen ? styles.open : ''].join(' ')}>▼</span>
      </button>

      {isOpen && (
        <ul className={styles.dropdown} role="listbox" aria-label={t('languageSwitcher.title')}>
          {LANGUAGE_OPTIONS.map((option) => (
            <li
              key={option.value}
              role="option"
              aria-selected={option.value === preference}
              className={[styles.option, option.value === preference ? styles.active : ''].join(' ')}
              onClick={() => handleSelect(option.value)}
            >
              <span className={styles.flag}>{option.flag}</span>
              <span className={styles.nativeLabel}>{option.nativeLabel}</span>
              {option.value === 'auto' && (
                <span className={styles.autoHint}>
                  ({autoResolved === 'zh-CN' ? '中文' : 'EN'})
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
