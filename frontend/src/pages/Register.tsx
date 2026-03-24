import { useState, FormEvent, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Toast } from '../components/common/Toast';
import { Lock, User, Mail, ArrowRight, Eye, EyeOff } from 'lucide-react';
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
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
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
      Toast.success('注册成功，即将跳转到登录页', 2500);
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

  const strengthColors = ['bg-transparent', 'bg-red-400', 'bg-amber-400', 'bg-emerald-400'];
  const strengthLabels = ['', '弱', '中', '强'];

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 relative overflow-hidden font-sans text-slate-800">
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
        @keyframes slideUpFade {
          from { opacity: 0; transform: translateY(15px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-slide-up {
          animation: slideUpFade 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        @keyframes gradientFlow {
          0% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        .animate-gradient-flow {
          background-size: 200% auto;
          animation: gradientFlow 3s linear infinite;
        }
        .animate-gradient-flow:hover {
          animation: gradientFlow 0.8s linear infinite;
        }
        .bg-multi-gradient {
          background-image: linear-gradient(to right,
            #0ea5e9, #8b5cf6, #ec4899, #f97316, #10b981,
            #0ea5e9, #8b5cf6, #ec4899, #f97316, #10b981
          );
        }
      ` }} />

      {/* 背景动态光斑 */}
      <div className="absolute top-0 -left-4 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-3xl opacity-60 animate-blob"></div>
      <div className="absolute top-0 -right-4 w-72 h-72 bg-indigo-300 rounded-full mix-blend-multiply filter blur-3xl opacity-60 animate-blob animation-delay-2000"></div>
      <div className="absolute -bottom-8 left-20 w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply filter blur-3xl opacity-60 animate-blob animation-delay-4000"></div>

      {/* 主卡片容器 */}
      <div className="relative z-10 w-full max-w-md p-8 sm:p-10 bg-white/70 backdrop-blur-xl rounded-[2rem] border border-white/60 shadow-xl mx-4">

        {/* 表单头部 */}
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-pink-500">
            创建账号
          </h2>
          <p className="text-slate-500 mt-2 text-sm">
            加入我们，开启一段全新的旅程
          </p>
        </div>

        {error && (
          <div className="mb-5 px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 animate-slide-up">
            {error}
          </div>
        )}

        {/* 表单内容 */}
        <form onSubmit={handleSubmit} className="space-y-5 animate-slide-up">
          {/* 用户名输入框 */}
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <User className="h-5 w-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
            </div>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="block w-full pl-11 pr-4 py-3 bg-white/80 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all placeholder-slate-400 text-slate-800 outline-none shadow-sm"
              placeholder="用户名"
              minLength={3}
              maxLength={20}
              required
            />
            <span className="block mt-1 text-xs text-slate-400 ml-1">3-20个字符</span>
          </div>

          {/* 邮箱输入框 */}
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Mail className="h-5 w-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
            </div>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={`block w-full pl-11 pr-4 py-3 bg-white/80 border rounded-xl transition-all placeholder-slate-400 text-slate-800 outline-none shadow-sm focus:ring-2 focus:ring-indigo-500 ${email && !emailValid ? 'border-red-400 focus:border-red-400 focus:ring-red-400' : 'border-slate-200 focus:border-indigo-500'}`}
              placeholder="电子邮箱"
              required
            />
            {email && !emailValid && (
              <span className="block mt-1 text-xs text-red-500 ml-1">请输入有效的邮箱地址</span>
            )}
          </div>

          {/* 密码输入框 */}
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
            </div>
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="block w-full pl-11 pr-12 py-3 bg-white/80 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all placeholder-slate-400 text-slate-800 outline-none shadow-sm"
              placeholder="密码"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 hover:text-slate-600 transition-colors outline-none"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>

          {/* 密码强度条 */}
          {password.length > 0 && (
            <div className="space-y-2 animate-slide-up">
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 rounded-full ${strengthColors[passwordStrength]}`}
                    style={{ width: passwordStrength === 1 ? '25%' : passwordStrength === 2 ? '60%' : passwordStrength === 3 ? '100%' : '0%' }}
                  />
                </div>
                <span className={`text-xs font-medium ${passwordStrength === 1 ? 'text-red-500' : passwordStrength === 2 ? 'text-amber-500' : 'text-emerald-500'}`}>
                  {strengthLabels[passwordStrength]}
                </span>
              </div>
              <div className="flex flex-wrap gap-x-3 gap-y-1">
                {passwordChecks.map((check, i) => (
                  <span
                    key={i}
                    className={`text-xs ${check.met ? 'text-emerald-500' : 'text-slate-400'}`}
                  >
                    {check.met ? '✓' : '○'} {check.label}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 确认密码输入框 */}
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
            </div>
            <input
              id="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="block w-full pl-11 pr-12 py-3 bg-white/80 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all placeholder-slate-400 text-slate-800 outline-none shadow-sm"
              placeholder="确认密码"
              required
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute inset-y-0 right-0 pr-4 flex items-center text-slate-400 hover:text-slate-600 transition-colors outline-none"
            >
              {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>

          {/* 提交按钮 */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-xl shadow-md text-sm font-bold text-white bg-multi-gradient animate-gradient-flow hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white focus:ring-indigo-500 transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
          >
            {isLoading ? '注册中...' : '注 册'}
            <ArrowRight className="ml-2 h-4 w-4" />
          </button>
        </form>

        {/* 底部链接 */}
        <p className="mt-6 text-center text-sm text-slate-500">
          已有账号？{' '}
          <Link to="/login" className="text-indigo-600 hover:text-indigo-500 font-medium transition-colors">
            立即登录
          </Link>
        </p>
      </div>
    </div>
  );
}
