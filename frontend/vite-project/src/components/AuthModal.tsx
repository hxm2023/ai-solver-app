/**
 * ==============================================================================
 * 用户认证组件 - 登录/注册模态框
 * ==============================================================================
 * 功能：
 * - 登录表单
 * - 注册表单
 * - JWT令牌管理
 * - 表单验证
 * ==============================================================================
 */

import React, { useState } from 'react';
import './AuthModal.css';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (user: any) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onLoginSuccess }) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [formData, setFormData] = useState({
    account: '',
    password: '',
    confirm_password: '',
    nickname: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 如果未打开，不渲染
  if (!isOpen) return null;

  // 处理输入变化
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError(''); // 清除错误提示
  };

  // 表单验证
  const validateForm = (): boolean => {
    if (!formData.account || formData.account.length < 3) {
      setError('账号长度至少3个字符');
      return false;
    }

    if (!formData.password || formData.password.length < 6) {
      setError('密码长度至少6个字符');
      return false;
    }

    if (mode === 'register') {
      if (formData.password !== formData.confirm_password) {
        setError('两次密码输入不一致');
        return false;
      }
      if (!formData.nickname || formData.nickname.length < 2) {
        setError('昵称长度至少2个字符');
        return false;
      }
    }

    return true;
  };

  // 处理登录
  const handleLogin = async () => {
    if (!validateForm()) return;

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://127.0.0.1:8000/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          account: formData.account,
          password: formData.password
        })
      });

      const data = await response.json();

      if (response.ok) {
        // 保存令牌和用户信息到localStorage
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('user_info', JSON.stringify(data.user_info));
        
        onLoginSuccess(data.user_info);
        onClose();
      } else {
        setError(data.detail || '登录失败，请检查账号密码');
      }
    } catch (err) {
      setError('网络错误，请检查后端服务是否启动');
      console.error('登录错误:', err);
    } finally {
      setLoading(false);
    }
  };

  // 处理注册
  const handleRegister = async () => {
    if (!validateForm()) return;

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://127.0.0.1:8000/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          account: formData.account,
          password: formData.password,
          nickname: formData.nickname
        })
      });

      const data = await response.json();

      if (response.ok) {
        // 注册成功后自动登录
        alert('注册成功！正在自动登录...');
        await handleLogin();
      } else {
        setError(data.detail || '注册失败');
      }
    } catch (err) {
      setError('网络错误，请检查后端服务是否启动');
      console.error('注册错误:', err);
    } finally {
      setLoading(false);
    }
  };

  // 提交表单
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (mode === 'login') {
      handleLogin();
    } else {
      handleRegister();
    }
  };

  // 切换模式
  const toggleMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setError('');
    setFormData({
      account: '',
      password: '',
      confirm_password: '',
      nickname: ''
    });
  };

  return (
    <div className="auth-modal-overlay" onClick={onClose}>
      <div className="auth-modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="auth-modal-close" onClick={onClose}>✕</button>
        
        <div className="auth-modal-header">
          <h2>{mode === 'login' ? '登录' : '注册'}</h2>
          <p className="auth-modal-subtitle">
            {mode === 'login' ? '欢迎回来！' : '创建您的账号'}
          </p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && (
            <div className="auth-error">
              ⚠️ {error}
            </div>
          )}

          <div className="auth-form-group">
            <label htmlFor="account">账号</label>
            <input
              type="text"
              id="account"
              name="account"
              value={formData.account}
              onChange={handleChange}
              placeholder="请输入账号（至少3个字符）"
              disabled={loading}
              autoComplete="username"
            />
          </div>

          <div className="auth-form-group">
            <label htmlFor="password">密码</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="请输入密码（至少6个字符）"
              disabled={loading}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </div>

          {mode === 'register' && (
            <>
              <div className="auth-form-group">
                <label htmlFor="confirm_password">确认密码</label>
                <input
                  type="password"
                  id="confirm_password"
                  name="confirm_password"
                  value={formData.confirm_password}
                  onChange={handleChange}
                  placeholder="请再次输入密码"
                  disabled={loading}
                  autoComplete="new-password"
                />
              </div>

              <div className="auth-form-group">
                <label htmlFor="nickname">昵称</label>
                <input
                  type="text"
                  id="nickname"
                  name="nickname"
                  value={formData.nickname}
                  onChange={handleChange}
                  placeholder="请输入昵称（至少2个字符）"
                  disabled={loading}
                />
              </div>
            </>
          )}

          <button 
            type="submit" 
            className="auth-submit-btn"
            disabled={loading}
          >
            {loading ? '处理中...' : (mode === 'login' ? '登录' : '注册')}
          </button>
        </form>

        <div className="auth-mode-switch">
          {mode === 'login' ? (
            <p>
              还没有账号？
              <button type="button" onClick={toggleMode} disabled={loading}>
                立即注册
              </button>
            </p>
          ) : (
            <p>
              已有账号？
              <button type="button" onClick={toggleMode} disabled={loading}>
                返回登录
              </button>
            </p>
          )}
        </div>

        {mode === 'login' && (
          <div className="auth-test-account">
            <p>💡 测试账号</p>
            <p>账号：demo_user</p>
            <p>密码：demo123456</p>
          </div>
        )}
      </div>
    </div>
  );
};

