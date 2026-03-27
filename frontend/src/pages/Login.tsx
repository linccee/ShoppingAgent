import { useState, FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { Toast } from '../components/common/Toast';
import { Lock, User, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { logger } from '../utils/logger';

export default function Login() {
  const { t } = useTranslation('auth');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      logger.info('Login', `Login attempt for user: ${username}`);
      await login(username, password);
      logger.info('Login', `Login successful for user: ${username}`);
      Toast.success(t('login.success'), 2500);
      navigate('/chat');
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: { message?: string } } } };
      const message =
        axiosError.response?.data?.detail?.message ||
        t('login.error');
      logger.error('Login', `Login failed for user: ${username}`, message);
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

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
            {t('login.title')}
          </h2>
          <p className="text-slate-500 mt-2 text-sm">
            {t('login.subtitle')}
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
              placeholder={t('login.username')}
              required
            />
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
              placeholder={t('login.password')}
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

          {/* 忘记密码 */}
          <div className="flex justify-end">
            <a href="#" className="text-sm text-indigo-600 hover:text-indigo-500 transition-colors">
              {t('login.forgotPassword')}
            </a>
          </div>

          {/* 提交按钮 */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-xl shadow-md text-sm font-bold text-white bg-multi-gradient animate-gradient-flow hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-white focus:ring-indigo-500 transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
          >
            {isLoading ? t('login.submitting') : t('login.submit')}
            <ArrowRight className="ml-2 h-4 w-4" />
          </button>
        </form>

        {/* 底部链接 */}
        <p className="mt-6 text-center text-sm text-slate-500">
          {t('login.noAccount')}{' '}
          <Link to="/register" className="text-indigo-600 hover:text-indigo-500 font-medium transition-colors">
            {t('login.registerNow')}
          </Link>
        </p>
      </div>
    </div>
  );
}
