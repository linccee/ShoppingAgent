import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from '../components/common/Button';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { userApi, UserPreferences, type LanguagePreference } from '../api/user';
import { LANGUAGE_OPTIONS } from '../i18n/constants';
import styles from './Profile.module.css';

export default function Profile() {
  const { t } = useTranslation('profile');
  const { user, logout } = useAuth();
  const { language: currentLang } = useLanguage();
  const navigate = useNavigate();

  const [preferences, setPreferences] = useState<UserPreferences>({
    default_currency: 'CNY',
    favorite_platforms: [],
    budget_range: { min: 0, max: 0 },
    notification_enabled: false,
    language_preference: 'auto',
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error'>('success');

  useEffect(() => {
    const loadUser = async () => {
      try {
        const response = await userApi.getCurrentUser();
        const prefs = response.data.preferences;
        setPreferences({
          default_currency: prefs.default_currency,
          favorite_platforms: prefs.favorite_platforms,
          budget_range: prefs.budget_range,
          notification_enabled: prefs.notification_enabled,
          language_preference: prefs.language_preference ?? 'auto',
        });
      } catch {
        // Ignore errors
      } finally {
        setIsLoading(false);
      }
    };
    void loadUser();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    setMessage('');
    try {
      await userApi.updatePreferences(preferences);
      setMessageType('success');
      setMessage(t('preferences.saveSuccess'));
    } catch {
      setMessageType('error');
      setMessage(t('preferences.saveError'));
    } finally {
      setIsSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (isLoading) {
    return <div className={styles.loading}>{t('loading')}</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <Button
            type="button"
            variant="ghost"
            className={styles.backButton}
            onClick={() => navigate('/chat')}
          >
            {t('back')}
          </Button>
          <h1 className={styles.title}>{t('title')}</h1>
        </div>

        {message && (
          <div className={messageType === 'success' ? styles.success : styles.error}>
            {message}
          </div>
        )}

        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>{t('account.title')}</h2>
          <div className={styles.info}>
            <div className={styles.infoRow}>
              <span className={styles.label}>{t('account.username')}</span>
              <span className={styles.value}>{user?.username}</span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.label}>{t('account.email')}</span>
              <span className={styles.value}>{user?.email}</span>
            </div>
          </div>
        </div>

        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>{t('preferences.title')}</h2>

          {/* 语言偏好 */}
          <div className={styles.field}>
            <label htmlFor="language">{t('preferences.language.label')}</label>
            <select
              id="language"
              value={preferences.language_preference}
              onChange={(e) =>
                setPreferences({
                  ...preferences,
                  language_preference: e.target.value as LanguagePreference,
                })
              }
              className={styles.select}
            >
              {LANGUAGE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.flag} {opt.nativeLabel}
                  {opt.value === 'auto' && ` (${currentLang === 'zh-CN' ? '中文' : 'EN'})`}
                </option>
              ))}
            </select>
            <p className={styles.fieldHint}>{t('preferences.language.description')}</p>
          </div>

          {/* 货币偏好 */}
          <div className={styles.field}>
            <label htmlFor="currency">{t('preferences.currency')}</label>
            <select
              id="currency"
              value={preferences.default_currency}
              onChange={(e) =>
                setPreferences({ ...preferences, default_currency: e.target.value })
              }
              className={styles.select}
            >
              <option value="CNY">人民币 (CNY)</option>
              <option value="USD">美元 (USD)</option>
              <option value="EUR">欧元 (EUR)</option>
            </select>
          </div>

          {/* 通知偏好 */}
          <div className={styles.field}>
            <label>
              <input
                type="checkbox"
                checked={preferences.notification_enabled}
                onChange={(e) =>
                  setPreferences({
                    ...preferences,
                    notification_enabled: e.target.checked,
                  })
                }
              />
              {t('preferences.notification')}
            </label>
          </div>

          <button
            onClick={handleSave}
            disabled={isSaving}
            className={styles.button}
          >
            {isSaving ? t('preferences.saving') : t('preferences.save')}
          </button>
        </div>

        <div className={styles.section}>
          <button onClick={handleLogout} className={styles.logoutButton}>
            {t('logout')}
          </button>
        </div>
      </div>
    </div>
  );
}
