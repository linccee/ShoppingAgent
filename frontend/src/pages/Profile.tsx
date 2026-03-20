import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { userApi, UserPreferences } from '../api/user';
import styles from './Profile.module.css';

export default function Profile() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [preferences, setPreferences] = useState<UserPreferences>({
    default_currency: 'CNY',
    favorite_platforms: [],
    budget_range: { min: 0, max: 0 },
    notification_enabled: false,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const loadUser = async () => {
      try {
        const response = await userApi.getCurrentUser();
        setPreferences(response.data.preferences);
      } catch {
        // Ignore errors
      } finally {
        setIsLoading(false);
      }
    };
    loadUser();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    setMessage('');
    try {
      await userApi.updatePreferences(preferences);
      setMessage('保存成功');
    } catch {
      setMessage('保存失败');
    } finally {
      setIsSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (isLoading) {
    return <div className={styles.loading}>加载中...</div>;
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>个人设置</h1>

        {message && (
          <div className={message.includes('成功') ? styles.success : styles.error}>
            {message}
          </div>
        )}

        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>账户信息</h2>
          <div className={styles.info}>
            <div className={styles.infoRow}>
              <span className={styles.label}>用户名</span>
              <span className={styles.value}>{user?.username}</span>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.label}>邮箱</span>
              <span className={styles.value}>{user?.email}</span>
            </div>
          </div>
        </div>

        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>偏好设置</h2>

          <div className={styles.field}>
            <label htmlFor="currency">默认货币</label>
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
              启用通知
            </label>
          </div>

          <button
            onClick={handleSave}
            disabled={isSaving}
            className={styles.button}
          >
            {isSaving ? '保存中...' : '保存设置'}
          </button>
        </div>

        <div className={styles.section}>
          <button onClick={handleLogout} className={styles.logoutButton}>
            退出登录
          </button>
        </div>
      </div>
    </div>
  );
}
