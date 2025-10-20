import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import MainApp from './MainApp.tsx'
import SimpleMistakeBook from './SimpleMistakeBook.tsx'
import './index.css'

// ============================================================
// 【新增】全局错误监听器 - 捕获所有未处理的错误
// ============================================================
window.addEventListener('error', (event) => {
  console.error('🔴 [全局错误] 未捕获的错误:', event.error);
  console.error('🔴 [全局错误] 错误信息:', event.message);
  console.error('🔴 [全局错误] 错误位置:', `${event.filename}:${event.lineno}:${event.colno}`);
  console.error('🔴 [全局错误] 堆栈信息:', event.error?.stack);
  
  // 将错误信息显示在页面上（便于非技术用户截图反馈）
  const errorDiv = document.createElement('div');
  errorDiv.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    max-width: 400px;
    background-color: #ff4444;
    color: white;
    padding: 15px;
    border-radius: 8px;
    z-index: 99999;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    font-family: monospace;
    font-size: 12px;
  `;
  errorDiv.innerHTML = `
    <strong>❌ 页面错误</strong><br/>
    ${event.message}<br/>
    <small>${event.filename}:${event.lineno}</small><br/>
    <button onclick="this.parentElement.remove()" style="margin-top:10px;padding:5px 10px;cursor:pointer;">
      关闭
    </button>
  `;
  document.body.appendChild(errorDiv);
  
  // 阻止默认错误处理（避免整个页面白屏）
  event.preventDefault();
});

// 捕获未处理的Promise拒绝
window.addEventListener('unhandledrejection', (event) => {
  console.error('🔴 [全局错误] 未处理的Promise拒绝:', event.reason);
  console.error('🔴 [全局错误] Promise:', event.promise);
  
  const errorDiv = document.createElement('div');
  errorDiv.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    max-width: 400px;
    background-color: #ff9800;
    color: white;
    padding: 15px;
    border-radius: 8px;
    z-index: 99999;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    font-family: monospace;
    font-size: 12px;
  `;
  errorDiv.innerHTML = `
    <strong>⚠️ 异步错误</strong><br/>
    ${event.reason?.message || event.reason}<br/>
    <button onclick="this.parentElement.remove()" style="margin-top:10px;padding:5px 10px;cursor:pointer;">
      关闭
    </button>
  `;
  document.body.appendChild(errorDiv);
  
  event.preventDefault();
});

console.log('✅ [全局错误监听] 已启用全局错误捕获机制');

// 根据URL参数决定加载哪个界面
// http://localhost:5173/?mode=old -> 原解题界面
// http://localhost:5173/?mode=new -> 带登录的个性化学习系统
// http://localhost:5173/ 或 ?mode=simple -> 简化版错题本（默认，无需登录）
const params = new URLSearchParams(window.location.search);
const mode = params.get('mode');

let AppToRender;
if (mode === 'old') {
  AppToRender = App;  // 原解题界面
} else if (mode === 'new') {
  AppToRender = MainApp;  // 带登录系统的界面
} else {
  AppToRender = SimpleMistakeBook;  // 默认：简化版错题本
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppToRender />
  </React.StrictMode>,
)