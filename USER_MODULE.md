# 用户模块技术规范

## 1. 概述

### 1.1 背景

当前系统使用基于 UUID 的匿名会话机制，所有用户共享同一个对话流程，无法区分不同使用者。用户模块的引入将实现：

- **用户身份识别**：区分不同用户的访问
- **会话隔离**：用户只能访问自己的历史会话
- **个性化设置**：保存用户偏好配置
- **数据安全**：保护用户隐私和对话历史

### 1.2 设计目标

1. **强制认证**：未登录用户无法使用任何功能（包括搜索、比价、推荐）
2. **用户隔离**：用户只能访问自己的历史会话和数据
3. **API 优先**：前后端分离架构，通过 RESTful API 通信
4. **安全优先**：专业级认证和授权机制

---

## 2. 架构设计

### 2.1 数据模型

#### 2.1.1 用户集合 (`users`)

```python
{
    "_id": ObjectId,
    "username": str,              # 唯一用户名 (3-20字符)
    "email": str,                 # 唯一邮箱
    "password_hash": str,         # 密码 bcrypt 哈希
    "created_at": datetime,
    "updated_at": datetime,
    "last_login": datetime,       # 最后登录时间
    "is_active": bool,           # 账号状态
    "role": str,                  # "user" | "admin"
    "preferences": {              # 用户偏好设置
        "default_currency": str,  # 默认货币 (CNY/USD/EUR)
        "favorite_platforms": [str],  # 常购平台
        "budget_range": {
            "min": int,
            "max": int
        },
        "notification_enabled": bool
    }
}
```

#### 2.1.2 用户会话关联 (`user_sessions`)

```python
{
    "_id": ObjectId,
    "user_id": ObjectId,          # 关联用户
    "session_id": str,            # 对话会话ID (引用 sessions collection)
    "created_at": datetime,
    "is_pinned": bool,            # 是否置顶
    "title": str                  # 会话标题
}
```

#### 2.1.3 现有集合变更

**`sessions` 集合新增字段**：

```python
{
    # ... 现有字段
    "user_id": ObjectId,          # 所属用户 (必需)
    "is_shared": bool,            # 是否共享给他人
    "shared_token": str | None,    # 分享令牌
    "device_id": str               # 设备标识 (用于迁移匿名会话)
}
```

### 2.2 模块结构

```
backend/
├── api/
│   └── v1/
│       ├── __init__.py
│       ├── auth.py          # 认证路由 (/api/v1/auth)
│       ├── users.py         # 用户路由 (/api/v1/users)
│       └── sessions.py      # 会话路由 (/api/v1/sessions)
├── core/
│   ├── __init__.py
│   ├── config.py           # 配置
│   ├── security.py         # JWT / 密码哈希
│   └── deps.py             # 依赖注入 (get_current_user)
├── models/
│   ├── __init__.py
│   ├── user.py             # 用户 MongoDB 模型
│   └── token.py            # Token 响应模型
├── repositories/
│   ├── __init__.py
│   └── user_repo.py        # 用户数据访问
├── services/
│   ├── __init__.py
│   ├── auth_service.py     # 认证业务逻辑
│   └── user_service.py    # 用户业务逻辑
└── main.py                 # FastAPI 应用入口

frontend/  (现有 Streamlit)
├── ui/
│   ├── auth.py             # 认证组件 (调用后端 API)
│   └── ...
└── ...
```

### 2.3 核心流程

#### 2.3.1 注册流程

```
用户输入 (username, email, password)
    ↓
密码强度校验 (≥8字符，含数字+字母)
    ↓
检查用户名/邮箱唯一性
    ↓
bcrypt 哈希密码
    ↓
存入 users 集合
    ↓
返回注册成功 / 错误信息
```

#### 2.3.2 登录流程

```
用户输入 (username/email, password)
    ↓
查找用户记录
    ↓
bcrypt 验证密码
    ↓
生成 JWT Token (包含 user_id, exp)
    ↓
更新 last_login 时间
    ↓
返回 Token + 用户信息
```

#### 2.3.3 会话关联流程

```
用户发起对话 (已登录)
    ↓
从 Header 提取 JWT Token
    ↓
解析 Token 获取 user_id
    ↓
创建新会话时关联 user_id
    ↓
查询历史会话时仅返回该用户的会话
```

---

## 3. API 设计

> 前缀：`/api/v1`（v1 表示 API 版本）

### 3.1 认证接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/v1/auth/register` | 用户注册 | 否 |
| POST | `/api/v1/auth/login` | 用户登录 | 否 |
| POST | `/api/v1/auth/refresh` | 刷新 Token | 是 |
| POST | `/api/v1/auth/logout` | 登出 | 是 |

#### 请求/响应示例

**POST /api/v1/auth/register**
```json
// Request
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123"
}

// Response 201
{
  "message": "注册成功",
  "user_id": "507f1f77bcf86cd799439011"
}
```

**POST /api/v1/auth/login**
```json
// Request
{
  "username": "john_doe",
  "password": "SecurePass123"
}

// Response 200
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

### 3.2 用户接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/v1/users/me` | 获取当前用户信息 | 是 |
| PUT | `/api/v1/users/me` | 更新用户信息 | 是 |
| PUT | `/api/v1/users/me/preferences` | 更新偏好设置 | 是 |
| DELETE | `/api/v1/users/me` | 删除账户 | 是 |

#### 请求/响应示例

**GET /api/v1/users/me**
```json
// Response 200
{
  "id": "507f1f77bcf86cd799439011",
  "username": "john_doe",
  "email": "john@example.com",
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-20T08:15:00Z",
  "is_active": true,
  "role": "user",
  "preferences": {
    "default_currency": "CNY",
    "favorite_platforms": ["amazon", "taobao"],
    "budget_range": {"min": 1000, "max": 5000},
    "notification_enabled": true
  }
}
```

### 3.3 会话接口

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| GET | `/api/v1/sessions` | 获取用户所有会话 | 是 |
| GET | `/api/v1/sessions/{session_id}` | 获取单个会话详情 | 是 |
| DELETE | `/api/v1/sessions/{session_id}` | 删除会话 | 是 |
| PUT | `/api/v1/sessions/{session_id}/pin` | 置顶/取消置顶 | 是 |
| POST | `/api/v1/sessions/{session_id}/share` | 生成分享链接 | 是 |

### 3.4 对话接口 (Agent)

| 方法 | 路径 | 描述 | 认证 |
|------|------|------|------|
| POST | `/api/v1/chat/sessions/{session_id}/messages` | 发送消息 | 是 |
| GET | `/api/v1/chat/sessions/{session_id}/messages` | 获取会话消息 | 是 |

### 3.5 错误响应格式

所有 API 统一错误格式：

```json
{
  "error": {
    "code": "AUTH_INVALID_CREDENTIALS",
    "message": "用户名或密码错误",
    "details": {}
  }
}
```

常见错误码：
- `AUTH_INVALID_CREDENTIALS` - 登录凭证无效
- `AUTH_USER_EXISTS` - 用户已存在
- `AUTH_WEAK_PASSWORD` - 密码强度不足
- `AUTH_UNAUTHORIZED` - 未提供/无效 Token
- `RESOURCE_NOT_FOUND` - 资源不存在
- `RESOURCE_FORBIDDEN` - 无权访问该资源

---

## 4. 安全设计

### 4.1 密码安全

- 使用 **bcrypt** 进行密码哈希（工作因子 12）
- 密码强度要求：至少 8 字符，包含数字和字母
- 禁止使用常见弱密码（前 1000 条）

### 4.2 Token 设计

```python
# JWT Payload
{
    "sub": "user_id",
    "username": "xxx",
    "exp": 1728000000,        # 7 天过期
    "iat": 1727376000
}
```

- Access Token：7 天有效期
- Token 存储在 HttpOnly Cookie（防 XSS）
- 敏感操作需重新验证密码

### 4.3 CORS 与速率限制

- 仅允许可信域名（配置化）
- 登录接口：5 次/分钟
- 注册接口：3 次/分钟
- 其他接口：60 次/分钟

---

## 5. 前端集成

> 技术栈：React 18 + TypeScript + Vite + Axios + React Router

### 5.1 前端架构

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  pages/     │  │components/ │  │     context/        │  │
│  │  Login.tsx  │  │ AuthForm   │  │  AuthContext.tsx    │  │
│  │  Chat.tsx   │  │ ChatBox    │  │  (全局状态管理)     │  │
│  │  Profile.tsx│  │ Sidebar    │  │                     │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┼─────────────────────┘             │
│                          │                                    │
│                    ┌─────▼─────┐                              │
│                    │  api/     │  (axios + Token 管理)        │
│                    │ client.ts │                              │
│                    └─────┬─────┘                              │
└──────────────────────────┼───────────────────────────────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │   FastAPI Backend   │
                 │   /api/v1/*         │
                 └─────────────────────┘
```

### 5.2 项目结构

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── api/
│   │   ├── client.ts         # Axios 实例 + 拦截器
│   │   ├── auth.ts           # 认证 API
│   │   ├── user.ts           # 用户 API
│   │   └── session.ts        # 会话 API
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── RegisterForm.tsx
│   │   ├── chat/
│   │   │   ├── ChatBox.tsx
│   │   │   ├── MessageList.tsx
│   │   │   └── InputBox.tsx
│   │   └── layout/
│   │       ├── Sidebar.tsx
│   │       └── Header.tsx
│   ├── context/
│   │   ├── AuthContext.tsx   # 认证状态管理
│   │   └── ChatContext.tsx   # 聊天状态管理
│   ├── pages/
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Chat.tsx
│   │   ├── History.tsx
│   │   └── Profile.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   └── useChat.ts
│   ├── types/
│   │   └── index.ts          # TypeScript 类型定义
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

### 5.3 API 客户端

`frontend/src/api/client.ts`：

```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';
import { useAuth } from '../context/AuthContext';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器：自动添加 Token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器：统一错误处理
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token 过期，清除本地状态
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  get instance() {
    return this.client;
  }

  get<T>(url: string, params?: object) {
    return this.client.get<T>(url, { params });
  }

  post<T>(url: string, data?: object) {
    return this.client.post<T>(url, data);
  }

  put<T>(url: string, data?: object) {
    return this.client.put<T>(url, data);
  }

  delete<T>(url: string) {
    return this.client.delete<T>(url);
  }
}

export const api = new APIClient();
export default api;
```

### 5.4 认证 API

`frontend/src/api/auth.ts`：

```typescript
import api from './client';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    username: string;
    email: string;
  };
}

export const authApi = {
  login: (data: LoginRequest) =>
    api.post<AuthResponse>('/auth/login', data),

  register: (data: RegisterRequest) =>
    api.post<{ message: string; user_id: string }>('/auth/register', data),

  refresh: () =>
    api.post<AuthResponse>('/auth/refresh'),

  logout: () =>
    api.post('/auth/logout'),
};
```

### 5.5 认证上下文

`frontend/src/context/AuthContext.tsx`：

```typescript
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi, AuthResponse } from '../api/auth';

interface User {
  id: string;
  username: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 初始化：从 localStorage 恢复登录状态
  useEffect(() => {
    const storedToken = localStorage.getItem('access_token');
    const storedUser = localStorage.getItem('user');

    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    const response = await authApi.login({ username, password });
    const { access_token, user: userData } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('user', JSON.stringify(userData));

    setToken(access_token);
    setUser(userData);
  };

  const register = async (username: string, email: string, password: string) => {
    await authApi.register({ username, email, password });
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
    authApi.logout();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### 5.6 登录页面

`frontend/src/pages/Login.tsx`：

```typescript
import { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(username, password);
      navigate('/chat');
    } catch (err: any) {
      const message = err.response?.data?.error?.message || '登录失败，请重试';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full p-8 bg-white rounded-lg shadow-md">
        <h1 className="text-2xl font-bold text-center mb-6">登录</h1>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-600 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">用户名</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium mb-1">密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? '登录中...' : '登录'}
          </button>
        </form>

        <p className="mt-4 text-center text-sm">
          还没有账号？<Link to="/register" className="text-blue-600 hover:underline">立即注册</Link>
        </p>
      </div>
    </div>
  );
}
```

### 5.7 私有路由包装

`frontend/src/components/PrivateRoute.tsx`：

```typescript
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function PrivateRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div>加载中...</div>;
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}
```

### 5.8 App 路由配置

`frontend/src/App.tsx`：

```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import PrivateRoute from './components/PrivateRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Chat from './pages/Chat';
import History from './pages/History';
import Profile from './pages/Profile';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* 公开路由 */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* 私有路由 */}
          <Route element={<PrivateRoute />}>
            <Route path="/chat" element={<Chat />} />
            <Route path="/history" element={<History />} />
            <Route path="/profile" element={<Profile />} />
          </Route>

          {/* 默认跳转 */}
          <Route path="/" element={<Navigate to="/chat" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
```

### 5.9 侧边栏组件

`frontend/src/components/layout/Sidebar.tsx`：

```typescript
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const navItems = [
    { path: '/chat', label: '对话', icon: '💬' },
    { path: '/history', label: '历史', icon: '📜' },
    { path: '/profile', label: '设置', icon: '⚙️' },
  ];

  return (
    <aside className="w-64 bg-white border-r h-screen flex flex-col">
      {/* 用户信息 */}
      <div className="p-4 border-b">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white">
            {user?.username?.[0]?.toUpperCase()}
          </div>
          <div>
            <p className="font-medium">{user?.username}</p>
            <p className="text-sm text-gray-500">{user?.email}</p>
          </div>
        </div>
      </div>

      {/* 导航 */}
      <nav className="flex-1 p-4">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center gap-2 px-3 py-2 rounded mb-1 ${
              location.pathname === item.path
                ? 'bg-blue-50 text-blue-600'
                : 'hover:bg-gray-50'
            }`}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      {/* 登出 */}
      <div className="p-4 border-t">
        <button
          onClick={logout}
          className="w-full px-3 py-2 text-red-600 hover:bg-red-50 rounded"
        >
          退出登录
        </button>
      </div>
    </aside>
  );
}
```

### 5.10 环境变量

`frontend/.env.development`：

```bash
VITE_API_URL=http://localhost:8000/api/v1
```

`frontend/.env.production`：

```bash
VITE_API_URL=https://your-domain.com/api/v1
```

### 5.11 依赖安装

```bash
# 创建项目
npm create vite@latest frontend -- --template react-ts

# 安装依赖
cd frontend
npm install axios react-router-dom

# 安装类型定义
npm install -D @types/react-router-dom

# 可选：UI 组件库
npm install antd        # 或
npm install tailwindcss postcss autoprefixer
```

---

## 6. 数据库迁移

### 6.1 初始化脚本

```python
# scripts/init_user_db.py

def migrate():
    # 1. 创建索引
    users.create_index("username", unique=True)
    users.create_index("email", unique=True)
    user_sessions.create_index("user_id")
    user_sessions.create_index([("user_id", 1), ("created_at", -1)])

    # 2. 迁移现有会话 (可选)
    # 将 anonymous sessions 标记为游客会话
    sessions.update_many(
        {"user_id": {"$exists": False}},
        {"$set": {"user_id": None}}
    )
```

---

## 7. 配置项

在 `config.py` 新增：

```python
class Config:
    # ... 现有配置

    # ── 用户模块配置 ──
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS = 7

    # 密码策略
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_DIGIT = True
    PASSWORD_REQUIRE_LETTER = True

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")

    # 速率限制
    LOGIN_RATE_LIMIT = 5  # 次/分钟
    REGISTER_RATE_LIMIT = 3
```

---

## 8. 环境变量

`.env` 新增：

```bash
# 用户模块
JWT_SECRET=your-256-bit-secret-key
CORS_ORIGINS=http://localhost:8501,https://yourdomain.com
```

---

## 9. 测试策略

### 9.1 单元测试

- `test_user_model.py`：数据模型验证
- `test_auth.py`：JWT 生成/验证
- `test_password.py`：密码哈希与验证

### 9.2 集成测试

- `test_user_api.py`：用户注册/登录 API
- `test_session_isolation.py`：用户会话隔离验证

### 9.3 E2E 测试

- 用户注册流程
- 用户登录流程
- 跨设备会话同步

---

## 10. 实施计划

### Phase 1：后端基础 (预计 2 天)

1. 创建 FastAPI 项目骨架 (`backend/`)
2. 实现用户模型和 MongoDB 仓储层
3. 实现 JWT 认证逻辑 (`core/security.py`)
4. 实现认证 API 路由 (`api/v1/auth.py`)
5. 编写单元测试

### Phase 2：后端业务 (预计 2 天)

1. 实现用户 API (`api/v1/users.py`)
2. 实现会话 API (`api/v1/sessions.py`)
3. 实现对话 API (`api/v1/chat.py`)
4. 添加认证中间件和依赖注入
5. 集成测试

### Phase 3：前端集成 (预计 2 天)

1. 初始化 React + TypeScript + Vite 项目
2. 创建 Axios API 客户端和认证拦截器
3. 实现 AuthContext 全局状态管理
4. 开发登录/注册页面和表单组件
5. 开发聊天页面 (Chat.tsx)
6. 实现私有路由和认证保护
7. 开发侧边栏和布局组件
8. 配置 Tailwind CSS 或 Ant Design

### Phase 4：测试与部署 (预计 1 天)

1. 端到端测试
2. 安全审计
3. 部署配置 (Docker/Nginx)

---

## 11. 数据迁移

从匿名会话迁移到用户会话：

```python
# 迁移脚本 - 将现有匿名会话关联到用户
def migrate_anonymous_sessions(user_id: str, device_id: str):
    """
    用户首次登录时，关联该设备上的匿名会话
    device_id: 设备指纹或浏览器标识
    """
    sessions_col.update_many(
        {"device_id": device_id, "user_id": None},
        {"$set": {"user_id": user_id}}
    )
```

---

## 12. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| JWT 泄露 | 账户被盗 | 使用 HttpOnly Cookie，Token 过期机制 |
| 密码破解 | 账户被盗 | bcrypt + 密码强度校验 + 登录限流 |
| MongoDB 性能 | 响应慢 | 关键字段索引 + 分页查询 |
| 并发冲突 | 数据丢失 | MongoDB 事务或乐观锁 |

---

## 附录 A：文件变更清单

### 后端 (backend/)

| 操作 | 文件路径 | 描述 |
|------|----------|------|
| 新增 | `backend/__init__.py` | 包初始化 |
| 新增 | `backend/main.py` | FastAPI 应用入口 |
| 新增 | `backend/core/__init__.py` | 核心模块 |
| 新增 | `backend/core/config.py` | 配置管理 |
| 新增 | `backend/core/security.py` | JWT / 密码安全 |
| 新增 | `backend/core/deps.py` | 依赖注入 |
| 新增 | `backend/core/database.py` | MongoDB 连接 |
| 新增 | `backend/models/__init__.py` | 数据模型 |
| 新增 | `backend/models/user.py` | 用户模型 |
| 新增 | `backend/models/token.py` | Token 模型 |
| 新增 | `backend/models/schemas.py` | Pydantic schemas |
| 新增 | `backend/repositories/__init__.py` | 仓储层 |
| 新增 | `backend/repositories/user_repo.py` | 用户仓储 |
| 新增 | `backend/repositories/session_repo.py` | 会话仓储 |
| 新增 | `backend/services/__init__.py` | 业务逻辑层 |
| 新增 | `backend/services/auth_service.py` | 认证服务 |
| 新增 | `backend/services/user_service.py` | 用户服务 |
| 新增 | `backend/api/__init__.py` | API 层 |
| 新增 | `backend/api/v1/__init__.py` | v1 版本 |
| 新增 | `backend/api/v1/auth.py` | 认证路由 |
| 新增 | `backend/api/v1/users.py` | 用户路由 |
| 新增 | `backend/api/v1/sessions.py` | 会话路由 |
| 新增 | `backend/api/v1/chat.py` | 对话路由 |

### 前端 (React)

| 操作 | 文件路径 | 描述 |
|------|----------|------|
| 新增 | `frontend/index.html` | HTML 入口 |
| 新增 | `frontend/vite.config.ts` | Vite 配置 |
| 新增 | `frontend/tsconfig.json` | TypeScript 配置 |
| 新增 | `frontend/package.json` | 依赖管理 |
| 新增 | `frontend/src/main.tsx` | React 入口 |
| 新增 | `frontend/src/App.tsx` | 路由配置 |
| 新增 | `frontend/src/api/client.ts` | Axios 封装 |
| 新增 | `frontend/src/api/auth.ts` | 认证 API |
| 新增 | `frontend/src/api/user.ts` | 用户 API |
| 新增 | `frontend/src/api/session.ts` | 会话 API |
| 新增 | `frontend/src/context/AuthContext.tsx` | 认证状态管理 |
| 新增 | `frontend/src/context/ChatContext.tsx` | 聊天状态管理 |
| 新增 | `frontend/src/pages/Login.tsx` | 登录页 |
| 新增 | `frontend/src/pages/Register.tsx` | 注册页 |
| 新增 | `frontend/src/pages/Chat.tsx` | 聊天页 |
| 新增 | `frontend/src/pages/History.tsx` | 历史会话页 |
| 新增 | `frontend/src/pages/Profile.tsx` | 个人设置页 |
| 新增 | `frontend/src/components/PrivateRoute.tsx` | 私有路由 |
| 新增 | `frontend/src/components/layout/Sidebar.tsx` | 侧边栏 |
| 新增 | `frontend/src/components/auth/LoginForm.tsx` | 登录表单 |
| 新增 | `frontend/src/components/auth/RegisterForm.tsx` | 注册表单 |
| 新增 | `frontend/src/components/chat/ChatBox.tsx` | 聊天组件 |
| 新增 | `frontend/src/types/index.ts` | 类型定义 |
| 新增 | `frontend/.env.development` | 开发环境变量 |
| 新增 | `frontend/.env.production` | 生产环境变量 |

### 测试

| 操作 | 文件路径 | 描述 |
|------|----------|------|
| 新增 | `test/test_auth_api.py` | 认证 API 测试 |
| 新增 | `test/test_user_api.py` | 用户 API 测试 |
| 新增 | `test/test_session_api.py` | 会话 API 测试 |
| 新增 | `test/conftest.py` | pytest fixtures |

### 脚本与配置

| 操作 | 文件路径 | 描述 |
|------|----------|------|
| 新增 | `scripts/init_user_db.py` | 数据库初始化 |
| 新增 | `Dockerfile.backend` | 后端容器化 |
| 新增 | `docker-compose.yml` | 编排配置 |
| 修改 | `config.py` | 添加后端配置 |
| 修改 | `.env.example` | 新增环境变量 |

---

## 附录 B：技术选型

| 类别 | 技术栈 | 理由 |
|------|--------|------|
| API 框架 | FastAPI | Python 生态、高性能、自动文档 |
| 认证 | JWT (python-jose) | 无状态、易扩展 |
| 密码哈希 | bcrypt | 安全、社区成熟 |
| 数据验证 | Pydantic | 类型安全、自动生成 JSON Schema |
| 数据库 | MongoDB | 复用现有、文档模型友好 |
| HTTP 客户端 | httpx | 异步支持、Python 3.7+ |
| 容器化 | Docker | 标准化部署 |
