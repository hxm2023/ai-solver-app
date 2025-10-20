// ==============================================================================
// MainApp.tsx - 主应用界面（整合所有功能）
// ==============================================================================

import React, { useState, useEffect } from 'react';
import LoginPage from './LoginPage';
import PersonalLearning from './PersonalLearning';
import './MainApp.css';

type AppView = 'solve' | 'review' | 'learning';

const MainApp: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [currentView, setCurrentView] = useState<AppView>('learning');

  // 检查是否已登录
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const savedUsername = localStorage.getItem('username');
    if (token && savedUsername) {
      setIsLoggedIn(true);
      setUsername(savedUsername);
    }
  }, []);

  const handleLogin = (token: string, user: string) => {
    setIsLoggedIn(true);
    setUsername(user);
  };

  const handleLogout = () => {
    if (confirm('确定要退出登录吗？')) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('username');
      setIsLoggedIn(false);
      setUsername('');
      setCurrentView('learning');
    }
  };

  // 未登录显示登录页面
  if (!isLoggedIn) {
    return <LoginPage onLoginSuccess={handleLogin} />;
  }

  // 已登录显示主界面
  return (
    <div className="main-app">
      {/* 顶部导航栏 */}
      <nav className="top-nav">
        <div className="nav-brand">
          <h1>🎓 沐梧AI学习系统</h1>
        </div>
        <div className="nav-menu">
          <button 
            className={currentView === 'solve' ? 'active' : ''}
            onClick={() => setCurrentView('solve')}
          >
            🧠 AI解题
          </button>
          <button 
            className={currentView === 'review' ? 'active' : ''}
            onClick={() => setCurrentView('review')}
          >
            📝 批改作业
          </button>
          <button 
            className={currentView === 'learning' ? 'active' : ''}
            onClick={() => setCurrentView('learning')}
          >
            📚 学习中心
          </button>
        </div>
        <div className="nav-user">
          <span className="username">👤 {username}</span>
          <button onClick={handleLogout} className="logout-button">
            退出
          </button>
        </div>
      </nav>

      {/* 主内容区 */}
      <main className="main-content">
        {currentView === 'learning' && <PersonalLearning />}
        
        {currentView === 'solve' && (
          <div className="coming-soon">
            <h2>🧠 AI智能解题</h2>
            <p>该功能即将整合到新界面</p>
            <p>目前请使用原有的解题界面</p>
            <button onClick={() => window.location.href = '/'} className="btn-primary">
              前往原解题界面
            </button>
          </div>
        )}
        
        {currentView === 'review' && (
          <div className="coming-soon">
            <h2>📝 AI批改作业</h2>
            <p>该功能即将整合到新界面</p>
            <p>目前请使用原有的批改界面</p>
            <button onClick={() => window.location.href = '/'} className="btn-primary">
              前往原批改界面
            </button>
          </div>
        )}
      </main>

      {/* 底部说明 */}
      <footer className="app-footer">
        <p>沐梧AI个性化学习系统 V23.0-F4-COMPLETE</p>
        <p>
          <a href="http://127.0.0.1:8000/docs" target="_blank">API文档</a> | 
          <a href="#" onClick={(e) => { e.preventDefault(); alert('功能开发中'); }}>帮助文档</a> | 
          <a href="#" onClick={(e) => { e.preventDefault(); alert('功能开发中'); }}>反馈建议</a>
        </p>
      </footer>
    </div>
  );
};

export default MainApp;

