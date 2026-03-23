import { useState, FormEvent, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import styles from './Register.module.css';
import { logger } from '../utils/logger';

function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

interface PasswordRequirement {
  label: string;
  test: (pwd: string) => boolean;
}

const passwordRequirements: PasswordRequirement[] = [
  { label: '至少8个字符', test: (pwd) => pwd.length >= 8 },
  { label: '包含大写字母', test: (pwd) => /[A-Z]/.test(pwd) },
  { label: '包含小写字母', test: (pwd) => /[a-z]/.test(pwd) },
  { label: '包含数字', test: (pwd) => /\d/.test(pwd) },
  { label: '包含特殊字符', test: (pwd) => /[^A-Za-z0-9]/.test(pwd) },
];

export default function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  const emailValid = useMemo(() => email.length === 0 || isValidEmail(email), [email]);
  const passwordChecks = useMemo(() => passwordRequirements.map((req) => ({
    ...req,
    met: req.test(password),
  })), [password]);
  const passwordStrength = useMemo(() => {
    const metCount = passwordChecks.filter((c) => c.met).length;
    if (password.length === 0) return 0;
    if (metCount <= 2) return 1;
    if (metCount <= 4) return 2;
    return 3;
  }, [passwordChecks, password.length]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      logger.warn('Register', 'Password mismatch');
      setError('两次输入的密码不一致');
      return;
    }

    if (password.length < 8) {
      logger.warn('Register', 'Password too short');
      setError('密码长度至少为8个字符');
      return;
    }

    setIsLoading(true);

    try {
      logger.info('Register', `Registration attempt for user: ${username}, email: ${email}`);
      await register(username, email, password);
      logger.info('Register', `Registration successful for user: ${username}`);
      navigate('/login');
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: { message?: string } } } };
      const message =
        axiosError.response?.data?.detail?.message ||
        '注册失败，请重试';
      logger.error('Register', `Registration failed for user: ${username}`, message);
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>注册</h1>

        {error && <div className={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label htmlFor="username">用户名</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={styles.input}
              minLength={3}
              maxLength={20}
              required
            />
            <span className={styles.hint}>3-20个字符</span>
          </div>

          <div className={styles.field}>
            <label htmlFor="email">邮箱</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={`${styles.input} ${email && !emailValid ? styles.inputError : ''}`}
              required
            />
            {email && !emailValid && (
              <span className={styles.fieldError}>请输入有效的邮箱地址</span>
            )}
          </div>

          <div className={styles.field}>
            <label htmlFor="password">密码</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={styles.input}
              minLength={8}
              required
            />
            {password.length > 0 && (
              <>
                <div className={styles.strengthBar}>
                  <div
                    className={`${styles.strengthFill} ${styles[`strength${passwordStrength}`]}`}
                  />
                </div>
                <div className={styles.requirements}>
                  {passwordChecks.map((check, i) => (
                    <span
                      key={i}
                      className={check.met ? styles.reqMet : styles.reqUnmet}
                    >
                      {check.met ? '✓' : '○'} {check.label}
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>

          <div className={styles.field}>
            <label htmlFor="confirmPassword">确认密码</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={styles.input}
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className={styles.button}
          >
            {isLoading ? '注册中...' : '注册'}
          </button>
        </form>

        <p className={styles.link}>
          已有账号？<Link to="/login">立即登录</Link>
        </p>
      </div>
    </div>
  );
}
