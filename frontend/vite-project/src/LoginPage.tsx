// ==============================================================================
// LoginPage.tsx - 用户登录/注册界面
// ==============================================================================

import React, { useState } from 'react';
import axios from 'axios';
import './LoginPage.css';

const API_BASE_URL = 'http://127.0.0.1:8000';

// 配置axios超时和拦截器
axios.defaults.timeout = 10000; // 10秒超时

// 请求拦截器 - 调试用
axios.interceptors.request.use(
  (config) => {
    console.log('🔵 Axios请求拦截器 - 请求配置:', config);
    return config;
  },
  (error) => {
    console.error('🔴 Axios请求拦截器 - 错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器 - 调试用
axios.interceptors.response.use(
  (response) => {
    console.log('🟢 Axios响应拦截器 - 响应:', response);
    return response;
  },
  (error) => {
    console.error('🔴 Axios响应拦截器 - 错误:', error);
    return Promise.reject(error);
  }
);

interface LoginPageProps {
  onLoginSuccess: (token: string, username: string) => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!username.trim() || !password.trim()) {
      setError('请输入用户名和密码');
      return;
    }

    setLoading(true);
    console.log('🚀 开始请求...', isLogin ? '登录' : '注册');
    console.log('📡 API地址:', API_BASE_URL);
    console.log('👤 用户名:', username);

    try {
      if (isLogin) {
        // 登录
        console.log('📤 发送登录请求...');
        const response = await axios.post(`${API_BASE_URL}/auth/login`, {
          username,
          password
        });
        console.log('✅ 登录成功:', response.data);
        const { access_token, user_info } = response.data;
        localStorage.setItem('auth_token', access_token);
        localStorage.setItem('username', user_info.username);
        onLoginSuccess(access_token, user_info.username);
      } else {
        // 注册
        console.log('📤 发送注册请求...');
        const response = await axios.post(`${API_BASE_URL}/auth/register`, {
          username,
          password
        });
        console.log('✅ 注册成功:', response.data);
        alert('注册成功！请登录');
        setIsLogin(true);
        setPassword('');
      }
    } catch (error: any) {
      console.error('❌ 请求失败:', error);
      console.error('❌ 错误详情:', {
        message: error.message,
        response: error.response,
        request: error.request,
        code: error.code
      });
      
      let errorMsg = '操作失败，请重试';
      if (error.response) {
        // 服务器返回错误响应
        errorMsg = error.response.data?.detail || `服务器错误: ${error.response.status}`;
      } else if (error.request) {
        // 请求已发送但没有收到响应
        errorMsg = '无法连接到服务器，请检查：\n1. 后端是否启动？\n2. 地址是否正确？';
      } else {
        // 请求配置出错
        errorMsg = `请求配置错误: ${error.message}`;
      }
      setError(errorMsg);
    } finally {
      setLoading(false);
      console.log('🏁 请求结束');
    }
  };

  // 快速测试登录
  const quickLogin = () => {
    setUsername('test_student');
    setPassword('password123');
    setIsLogin(true);
  };

  // 测试后端连接
  const testBackendConnection = async () => {
    console.log('🧪 测试后端连接...');
    try {
      const response = await axios.get(`${API_BASE_URL}/`);
      console.log('✅ 后端连接成功:', response.data);
      alert('✅ 后端连接正常！\n' + JSON.stringify(response.data, null, 2));
    } catch (error: any) {
      console.error('❌ 后端连接失败:', error);
      alert('❌ 后端连接失败！\n' + error.message);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1>🎓 沐梧AI学习系统</h1>
          <p>个性化智能学习平台</p>
        </div>

        <div className="login-tabs">
          <button 
            className={isLogin ? 'active' : ''}
            onClick={() => setIsLogin(true)}
          >
            登录
          </button>
          <button 
            className={!isLogin ? 'active' : ''}
            onClick={() => setIsLogin(false)}
          >
            注册
          </button>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label>用户名</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="请输入用户名"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label>密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="请输入密码"
              disabled={loading}
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button 
            type="submit" 
            className="submit-button"
            disabled={loading}
          >
            {loading ? '处理中...' : (isLogin ? '登录' : '注册')}
          </button>
        </form>

        <div className="quick-login">
          <button onClick={testBackendConnection} className="quick-login-button" style={{marginBottom: '10px', background: '#4CAF50'}}>
            🧪 测试后端连接
          </button>
          <button onClick={quickLogin} className="quick-login-button">
            ⚡ 快速测试登录
          </button>
          <p className="quick-login-hint">
            用户名: test_student | 密码: password123
          </p>
        </div>

        <div className="login-footer">
          <p>🎉 功能特色</p>
          <ul>
            <li>📚 智能错题本 - 自动记录和管理</li>
            <li>🎯 AI智能出题 - 针对性练习</li>
            <li>📄 试卷生成 - 一键导出PDF</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;

