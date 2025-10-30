// ==============================================================================
// AppDB.tsx - 数据库版本【完全基于 App.tsx + 登录注册 + MySQL存储】
// 核心原则：保持App.tsx的所有功能和UI，只添加登录和数据库存储
// ==============================================================================

import React, { useState, useRef, useEffect } from 'react';
import { marked } from 'marked';
import './App.css';
import './ModeSelector.css';

// 配置marked以保护LaTeX公式
marked.setOptions({
  breaks: true,
  gfm: true,
  pedantic: false,
  sanitize: false,
  smartLists: true,
  smartypants: false, // 关键：不要转换引号和破折号，避免破坏LaTeX
});

import ReactCrop, { type Crop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import SimpleMistakeBookDB from './SimpleMistakeBookDB';

// 声明全局MathJax对象
declare global {
  interface Window { MathJax: any; }
}

// --- 【新增】React错误边界组件 ---
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    console.error('🔴 [ErrorBoundary] 捕获到渲染错误:', error);
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('🔴 [ErrorBoundary] 错误详情:', error);
    console.error('🔴 [ErrorBoundary] 组件堆栈:', errorInfo.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '20px',
          margin: '20px',
          border: '2px solid #ff4444',
          borderRadius: '8px',
          backgroundColor: '#fff5f5'
        }}>
          <h2>😔 页面渲染出错</h2>
          <p>错误信息：{this.state.error?.message || '未知错误'}</p>
          <button 
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            style={{
              padding: '10px 20px',
              fontSize: '16px',
              cursor: 'pointer',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px'
            }}
          >
            🔄 刷新页面
          </button>
          <details style={{ marginTop: '20px', fontSize: '12px' }}>
            <summary>技术详情（点击展开）</summary>
            <pre style={{ 
              backgroundColor: '#f5f5f5', 
              padding: '10px', 
              overflow: 'auto',
              maxHeight: '200px'
            }}>
              {this.state.error?.stack || '无堆栈信息'}
            </pre>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}

// --- 类型定义 ---
type Message = {
  role: 'user' | 'assistant';
  content: string;
};

type SessionInfo = {
  sessionId: string;
  title: string;
  timestamp: number;
  mode: 'solve' | 'review';
  imageSrc?: string;
  messages?: Message[];
};

interface MainAppProps {
  mode: 'solve' | 'review' | 'mistakeBook';
  onBack: () => void;
  userId: string;
  token: string;
  onLogout: () => void;
}

// --- 【数据库版本】会话管理工具函数 ---
const backendUrl = 'http://127.0.0.1:8000';

async function getSessions(userId: string, token: string, mode: 'solve' | 'review'): Promise<SessionInfo[]> {
  try {
    const response = await fetch(`${backendUrl}/api/db/sessions?mode=${mode}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    if (!response.ok) return [];
    const data = await response.json();
    return data.sessions || [];
  } catch (err) {
    console.error('[会话加载失败]', err);
    return [];
  }
}

async function saveSessionToDB(userId: string, token: string, session: SessionInfo): Promise<void> {
  try {
    await fetch(`${backendUrl}/api/db/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(session)
    });
  } catch (err) {
    console.error('[会话保存失败]', err);
  }
}

async function deleteSessionFromDB(userId: string, token: string, sessionId: string): Promise<void> {
  try {
    await fetch(`${backendUrl}/api/db/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
  } catch (err) {
    console.error('[会话删除失败]', err);
  }
}

// --- 【新增】登录注册组件 ---
interface AuthScreenProps {
  onLoginSuccess: (userId: string, token: string) => void;
}

const AuthScreen: React.FC<AuthScreenProps> = ({ onLoginSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [account, setAccount] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    setError('');
    
    if (!account || !password) {
      setError('请输入账号和密码');
      return;
    }
    
    if (!isLogin && password !== confirmPassword) {
      setError('两次密码不一致');
      return;
    }
    
    setLoading(true);
    
    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const response = await fetch(`${backendUrl}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(isLogin ? { account, password } : { account, password, name: name || account })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        setError(data.detail || '操作失败');
        setLoading(false);
        return;
      }
      
      // 登录/注册成功
      if (isLogin) {
        // 后端返回格式：{ access_token, token_type, user_info: { user_id, account } }
        console.log('✅ [登录成功]', {
          access_token: data.access_token ? `${data.access_token.substring(0, 20)}...` : 'undefined',
          user_id: data.user_info?.user_id || 'undefined',
          account: data.user_info?.account || 'undefined'
        });
        
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('userId', data.user_info.user_id);
        
        console.log('✅ [Token已保存到localStorage]');
        
        onLoginSuccess(data.user_info.user_id, data.access_token);
      } else {
        // 注册成功后自动登录
        setIsLogin(true);
        setError('');
        alert('注册成功！请登录');
      }
    } catch (err) {
      setError('网络错误，请检查后端服务');
      console.error('[认证错误]', err);
    }
    
    setLoading(false);
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '40px',
        width: '100%',
        maxWidth: '400px',
        boxShadow: '0 10px 40px rgba(0,0,0,0.2)'
      }}>
        <h1 style={{ textAlign: 'center', marginBottom: '30px', color: '#333' }}>
          {isLogin ? '登录' : '注册'} - 沐梧AI
        </h1>
        
        {error && (
          <div style={{
            padding: '10px',
            background: '#fee',
            border: '1px solid #fcc',
            borderRadius: '6px',
            marginBottom: '20px',
            color: '#c00'
          }}>
            {error}
          </div>
        )}
        
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>账号</label>
          <input
            type="text"
            value={account}
            onChange={e => setAccount(e.target.value)}
            placeholder="请输入账号"
            style={{
              width: '100%',
              padding: '12px',
              border: '1px solid #ddd',
              borderRadius: '6px',
              fontSize: '14px',
              boxSizing: 'border-box'
            }}
          />
        </div>
        
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>密码</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="请输入密码"
            style={{
              width: '100%',
              padding: '12px',
              border: '1px solid #ddd',
              borderRadius: '6px',
              fontSize: '14px',
              boxSizing: 'border-box'
            }}
          />
        </div>
        
        {!isLogin && (
          <>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>确认密码</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="请再次输入密码"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px',
                  boxSizing: 'border-box'
                }}
              />
            </div>
            
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>昵称（可选）</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="请输入昵称"
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px',
                  boxSizing: 'border-box'
                }}
              />
            </div>
          </>
        )}
        
        <button
          onClick={handleSubmit}
          disabled={loading}
          style={{
            width: '100%',
            padding: '14px',
            background: loading ? '#999' : 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            fontSize: '16px',
            fontWeight: 'bold',
            cursor: loading ? 'not-allowed' : 'pointer',
            marginBottom: '15px'
          }}
        >
          {loading ? '处理中...' : (isLogin ? '登录' : '注册')}
        </button>
        
        <div style={{ textAlign: 'center' }}>
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
            }}
            style={{
              background: 'none',
              border: 'none',
              color: '#667eea',
              cursor: 'pointer',
              fontSize: '14px',
              textDecoration: 'underline'
            }}
          >
            {isLogin ? '还没有账号？立即注册' : '已有账号？立即登录'}
          </button>
        </div>
      </div>
    </div>
  );
};

// --- 模式选择器组件 ---
interface ModeSelectorProps {
  onSelectMode: (mode: 'solve' | 'review' | 'mistakeBook') => void;
  onLogout: () => void;
}
const ModeSelector: React.FC<ModeSelectorProps> = ({ onSelectMode, onLogout }) => {
  return (
    <div className="mode-selector-container">
      <div className="mode-selector-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h1 className="mode-selector-title">请选择功能模式</h1>
          <button
            onClick={onLogout}
            style={{
              padding: '8px 16px',
              background: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            退出登录
          </button>
        </div>
        <p className="mode-selector-subtitle">你想让AI为你解答难题，还是批改你的作业？</p>
        <div className="mode-buttons">
          <button className="mode-button" onClick={() => onSelectMode('solve')}>
            <span className="button-icon">🧠</span>
            <div>
              <span className="button-text">AI 智能解题</span>
              <span className="button-description">上传题目，获取详细解答</span>
            </div>
          </button>
          <button className="mode-button" onClick={() => onSelectMode('review')}>
            <span className="button-icon">📝</span>
            <div>
              <span className="button-text">AI 批改作业</span>
              <span className="button-description">上传包含题目与答案的图片，获取专业点评</span>
            </div>
          </button>
          <button className="mode-button" onClick={() => onSelectMode('mistakeBook')}>
            <span className="button-icon">📚</span>
            <div>
              <span className="button-text">智能错题本</span>
              <span className="button-description">管理错题，AI生成针对性练习</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

// ==============================================================================
// MainApp组件 - 【完全复制 App.tsx 逻辑，只修改API调用】
// ==============================================================================

function MainApp({ mode, onBack, userId, token, onLogout }: MainAppProps) {
  // 如果是错题本模式，直接渲染SimpleMistakeBookDB
  if (mode === 'mistakeBook') {
    return (
      <div style={{ minHeight: '100vh', background: '#f5f5f5' }}>
        <div style={{
          background: 'white',
          padding: '15px 20px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          marginBottom: '0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <button
            onClick={onBack}
            style={{
              padding: '8px 20px',
              background: '#5C6AC4',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 'bold'
            }}
          >
            ← 返回主菜单
          </button>
          <h2 style={{ margin: 0, color: '#333' }}>📚 智能错题本</h2>
          <button
            onClick={onLogout}
            style={{
              padding: '8px 20px',
              background: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            退出登录
          </button>
        </div>
        <SimpleMistakeBookDB userId={userId} token={token} />
      </div>
    );
  }
  
  // --- 状态管理（完全复制 App.tsx）---
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatImageSrc, setChatImageSrc] = useState<string>('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [chatTitle, setChatTitle] = useState<string>("新对话");
  const [userInput, setUserInput] = useState<string>('');
  const [solveType, setSolveType] = useState<'single' | 'full' | 'specific'>('single');
  const [specificQuestion, setSpecificQuestion] = useState<string>('');

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [statusText, setStatusText] = useState<string>('');
  const [showQuickButtons, setShowQuickButtons] = useState<boolean>(false);
  
  const [imageSrc, setImageSrc] = useState<string>('');
  const [crop, setCrop] = useState<Crop>();
  const [isUploading, setIsUploading] = useState<boolean>(true);
  
  // --- 【新增】侧边栏相关状态 ---
  const [showSidebar, setShowSidebar] = useState<boolean>(false);
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  
  const imgRef = useRef<HTMLImageElement | null>(null);
  const fileRef = useRef<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  // --- 【修复】参考本地版本的简单有效方法 ---
  useEffect(() => {
    if (messages.length > 0) {
      // 延迟100ms后渲染公式（参考本地版本）
      setTimeout(() => {
        const answerDivs = document.querySelectorAll('.message-content');
        if (answerDivs.length > 0 && window.MathJax?.typesetPromise) {
          window.MathJax.typesetPromise(Array.from(answerDivs))
            .then(() => console.log('✅ [MathJax] 公式渲染完成'))
            .catch((err: any) => console.error('❌ [MathJax] 渲染错误:', err));
        }
      }, 100);
    }
  }, [messages]);
  
  // 滚动到底部
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // --- 【新增】加载会话列表（从数据库）---
  useEffect(() => {
    console.log('📋 [useEffect] 加载会话列表 (数据库), mode:', mode);
    (async () => {
      try {
        const allSessions = await getSessions(userId, token, mode);
        setSessions(allSessions);
        console.log('✅ [会话列表] 加载成功, 数量:', allSessions.length);
      } catch (err) {
        console.error('❌ [会话列表] 加载失败:', err);
      }
    })();
  }, [mode, userId, token]);
  
  // --- 【新增】保存当前会话到数据库 ---
  useEffect(() => {
    if (sessionId && chatTitle && chatImageSrc && messages.length > 0) {
      console.log('💾 [useEffect] 保存会话到数据库, sessionId:', sessionId);
      (async () => {
        try {
          await saveSessionToDB(userId, token, {
            sessionId,
            title: chatTitle,
            timestamp: Date.now(),
            mode,
            imageSrc: chatImageSrc,
            messages: messages
          });
          // 刷新会话列表
          const updatedSessions = await getSessions(userId, token, mode);
          setSessions(updatedSessions);
          console.log('✅ [会话保存] 成功');
        } catch (err) {
          console.error('❌ [会话保存] 失败:', err);
        }
      })();
    }
  }, [sessionId, chatTitle, chatImageSrc, messages, mode, userId, token]);

  // --- 核心逻辑函数（修改API URL，添加JWT认证）---
  const sendMessage = async (prompt: string, imageBlob?: Blob | File) => {
    console.log('[sendMessage] 开始, imageBlob存在:', !!imageBlob);
    
    setIsLoading(true);
    setError('');
    setShowQuickButtons(false);
    setStatusText('正在连接AI...');
    
    const isFirstMessage = !!imageBlob;
    console.log('[sendMessage] isFirstMessage:', isFirstMessage);
    
    // 添加用户消息到UI
    const userMessage = { role: 'user' as const, content: prompt };
    if (!imageBlob) {
      setMessages(prev => [...prev, userMessage]);
    } else {
      setMessages([userMessage]);
    }
    setUserInput('');

    let currentSessionId = sessionId;
    let hasError = false;

    try {
      // 准备图片数据
      let imageBase64: string | undefined = undefined;
      if (imageBlob) {
        imageBase64 = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
          reader.onerror = reject;
          reader.readAsDataURL(imageBlob);
        });
        console.log('[sendMessage] 图片转换为Base64完成');
      }

      // 构建请求体
      const requestBody = {
        session_id: currentSessionId,
        prompt: prompt,
        image_base64: imageBase64,
        mode: mode // 添加模式参数
      };

      console.log('[sendMessage] 请求体构建完成');
      console.log('[sendMessage] Token存在:', !!token, token ? `${token.substring(0, 20)}...` : 'undefined');
      
      // 【修改】使用数据库API，添加JWT认证
      const response = await fetch(`${backendUrl}/api/db/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` // JWT认证
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();
      
      console.log('[DEBUG] ========== 收到后端响应 ==========');
      console.log('[DEBUG] response.ok:', response.ok);
      console.log('[DEBUG] data:', data);
      console.log('[DEBUG] =====================================');
      
      // 检查HTTP错误
      if (!response.ok) {
        if (response.status === 401) {
          alert('登录已过期，请重新登录');
          onLogout();
          return;
        }
        if (response.status === 404) {
          throw new Error(`404: ${data.detail || '会话已失效'}`);
        }
        throw new Error(`HTTP error! status: ${response.status}, ${data.detail || ''}`);
      }
      
      // 处理session_id
      if (data.session_id && !currentSessionId) {
        currentSessionId = data.session_id;
        setSessionId(data.session_id);
        if (data.title) setChatTitle(data.title);
        console.log('[会话] 新会话创建成功，session_id:', data.session_id);
      }
      
      // 处理错误
      if (data.error) {
        console.log('[DEBUG] 后端返回错误:', data.error);
        setError(`错误: ${data.error}`);
        hasError = true;
      } else {
        // 显示完整回答
        let fullContent = data.response || '';
        
        // 【新增】如果错题已自动保存，添加提示信息
        if (data.mistake_saved && data.knowledge_points && data.knowledge_points.length > 0) {
          const knowledgePointsText = data.knowledge_points.join('、');
          const mistakeSavedNotice = `\n\n---\n\n✅ **此题已自动保存到错题本**\n\n📌 **知识点标签**：${knowledgePointsText}\n\n💡 前往"智能错题本"模块可查看和管理错题，或基于错题生成练习试卷。`;
          fullContent = fullContent.replace("[MISTAKE_DETECTED]", "").trim() + mistakeSavedNotice;
        } else {
          fullContent = fullContent.replace("[MISTAKE_DETECTED]", "").replace("[CORRECT]", "").trim();
        }
        
        console.log('📦 [消息更新] fullContent 长度:', fullContent?.length);
        
        try {
          if (!imageBlob) {
            console.log('📝 [消息更新] 追问模式 - 追加AI回答');
            setMessages(prev => {
              const newMessages = [...prev, { role: 'assistant' as const, content: fullContent }];
              console.log('  📝 [状态更新] 更新后消息数:', newMessages.length);
              return newMessages;
            });
          } else {
            console.log('📝 [消息更新] 首次提问 - 创建新消息列表');
            const newMessages: Message[] = [
              userMessage, 
              { role: 'assistant' as const, content: fullContent }
            ];
            setMessages(newMessages);
          }
        } catch (updateErr) {
          console.error('❌ [消息更新] setMessages调用失败:', updateErr);
          throw updateErr;
        }
      }

    } catch (err) {
      hasError = true;
      let detail = "未知错误";
      
      if (err instanceof Error && err.message.includes('404')) {
        console.log('[错误] 会话已失效');
        setError(`会话已失效（可能是服务重启），请点击右上角"新对话"按钮重新开始`);
        setSessionId(null);
        setChatTitle("新对话");
        
        setTimeout(() => {
          setMessages([]);
          setIsUploading(true);
          setError('');
        }, 3000);
      } else {
        if (err instanceof Error) {
          detail = err.message;
        }
        setError(`糟糕，出错了！错误详情: ${detail}`);
        console.error("请求错误:", err);
      }
      
      // 如果出错，移除用户消息
      if (!imageBlob) {
        setMessages(prev => prev.slice(0, -1));
      } else {
        setMessages([]);
      }
    }
    
    setIsLoading(false);
    setStatusText('');
    
    // 【修复】每次AI回答后都显示快捷按钮（不限于第一次）
    if (!hasError && messages.length > 0) {
      console.log('✅ AI回答完成，显示快捷按钮');
      setShowQuickButtons(true);
    }
  };

  // 快捷按钮处理函数
  const handleQuickButtonClick = (message: string) => {
    sendMessage(message);
  };

  const handleInitialSend = (imageBlob: Blob | File, imageSrcForDisplay: string) => {
      console.log('[DEBUG] ========== handleInitialSend 调用 ==========');
      
      let promptText = '';
      // 根据模式和solveType，动态生成初始prompt
      if (solveType === 'single') {
        promptText = mode === 'solve' 
          ? '请认真审题并详细解答，写出完整的解题过程和思路。' 
          : '请认真批改这道题目，指出答案中的对错，如果答案错误就给出正确解法，回答正确就不用多说。';
      } else if (solveType === 'full') {
        promptText = mode === 'solve' 
          ? '请逐题解答，每道题都要写出详细的解题步骤和思路。' 
          : '请逐题批改，对每道题的答案指出答案中的对错，如果答案错误就给出正确解法，回答正确就不用多说。';
      } else { // specific
        if (!specificQuestion) { setError('请输入你要指定的题目信息。'); return; }
        const basePrompt = mode === 'solve' 
          ? '请只解答以下指定的题目，写出详细步骤：' 
          : '请只批改以下指定的题目，指出答案中的对错，如果答案错误就给出正确解法，回答正确就不用多说：';
        promptText = `${basePrompt}${specificQuestion}`;
      }
      
      setChatImageSrc(imageSrcForDisplay);
      setIsUploading(false);
      sendMessage(promptText, imageBlob);
  };
  
  const onSelectFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      fileRef.current = file;
      const reader = new FileReader();
      reader.addEventListener('load', () => setImageSrc(reader.result?.toString() || ''));
      reader.readAsDataURL(file);
    }
  };

  const handleCropAndSend = () => {
    if (!crop || !imgRef.current || !crop.width || !crop.height) {
      setError('请先在图片上拖动以选择一个裁剪区域。');
      return;
    }
    const canvas = document.createElement('canvas');
    const scaleX = imgRef.current.naturalWidth / imgRef.current.width;
    const scaleY = imgRef.current.naturalHeight / imgRef.current.height;
    canvas.width = Math.floor(crop.width * scaleX);
    canvas.height = Math.floor(crop.height * scaleY);
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      setError('无法处理图片，浏览器支持不足。');
      return;
    }
    ctx.drawImage(imgRef.current, crop.x * scaleX, crop.y * scaleY, crop.width * scaleX, crop.height * scaleY, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (blob) {
        const croppedImageSrc = canvas.toDataURL('image/png');
        handleInitialSend(blob, croppedImageSrc);
      }
    }, 'image/png');
  };
  
  // --- 会话管理处理函数（数据库版本）---
  const handleLoadSession = async (session: SessionInfo) => {
    console.log('[会话恢复] 开始加载会话:', session.sessionId);
    
    // 验证并清理消息数据
    const validMessages = (session.messages || []).filter((msg): msg is Message => {
      return msg && 
             typeof msg === 'object' && 
             (msg.role === 'user' || msg.role === 'assistant') && 
             typeof msg.content === 'string';
    });
    
    console.log('[会话恢复] 有效消息数:', validMessages.length);
    
    // 恢复前端状态
    setSessionId(session.sessionId);
    setChatTitle(session.title);
    setChatImageSrc(session.imageSrc || '');
    setIsUploading(false);
    setMessages(validMessages);
    setShowSidebar(false);
  };
  
  const handleDeleteSession = async (sessionIdToDelete: string) => {
    await deleteSessionFromDB(userId, token, sessionIdToDelete);
    const updatedSessions = await getSessions(userId, token, mode);
    setSessions(updatedSessions);
    
    console.log('[会话删除] 已删除会话:', sessionIdToDelete);
    
    // 如果删除的是当前会话，回到上传界面
    if (sessionIdToDelete === sessionId) {
      setSessionId(null);
      setChatTitle("新对话");
      setChatImageSrc('');
      setMessages([]);
      setIsUploading(true);
    }
  };
  
  const handleNewChat = () => {
    setSessionId(null);
    setChatTitle("新对话");
    setChatImageSrc('');
    setMessages([]);
    setIsUploading(true);
    setImageSrc('');
    setCrop(undefined);
    setShowSidebar(false);
  };

  // ==============================================================================
  // UI渲染（完全复制 App.tsx 的JSX）
  // ==============================================================================
  return (
    <div className="App">
      <header className="App-header">
        <button onClick={onBack} className="back-button">返回</button>
        <h1>{isUploading ? (mode === 'solve' ? 'AI 智能解题' : 'AI 批改作业') : chatTitle}</h1>
        <div className="header-actions">
          <button onClick={() => setShowSidebar(!showSidebar)} className="history-button">
            📚 历史记录
          </button>
          {!isUploading && (
            <button onClick={handleNewChat} className="new-chat-button">
              ➕ 新对话
            </button>
          )}
          <button
            onClick={onLogout}
            style={{
              padding: '8px 16px',
              background: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              marginLeft: '10px'
            }}
          >
            退出
          </button>
        </div>
      </header>
      
      {/* --- 侧边栏 --- */}
      {showSidebar && (
        <>
          <div className="sidebar-overlay" onClick={() => setShowSidebar(false)}></div>
          <div className="sidebar">
            <div className="sidebar-header">
              <h2>历史记录</h2>
              <button className="sidebar-close" onClick={() => setShowSidebar(false)}>✕</button>
            </div>
            <div className="sidebar-content">
              {sessions.length === 0 ? (
                <div className="no-sessions">
                  <p>暂无历史记录</p>
                  <p className="hint">开始解题后，这里会显示历史对话</p>
                </div>
              ) : (
                <div className="session-list">
                  {sessions.map((session) => (
                    <div 
                      key={session.sessionId} 
                      className={`session-item ${session.sessionId === sessionId ? 'active' : ''}`}
                    >
                      <div className="session-preview" onClick={() => handleLoadSession(session)}>
                        {session.imageSrc && (
                          <img src={session.imageSrc} alt="题目预览" className="session-thumbnail" />
                        )}
                        <div className="session-info">
                          <h3>{session.title}</h3>
                          <p className="session-time">
                            {new Date(session.timestamp).toLocaleString('zh-CN', {
                              month: 'numeric',
                              day: 'numeric',
                              hour: 'numeric',
                              minute: 'numeric'
                            })}
                          </p>
                        </div>
                      </div>
                      <button 
                        className="session-delete" 
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm('确定要删除这个会话吗？')) {
                            handleDeleteSession(session.sessionId);
                          }
                        }}
                      >
                        🗑️
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
      
      <main className="App-main">
        {error && <div className="error">{error}</div>}

        {isUploading ? (
          <div className="card-container">
            <div className="solve-type-selector">
              <button className={solveType === 'single' ? 'active' : ''} onClick={() => setSolveType('single')}>解/改单个题目</button>
              <button className={solveType === 'full' ? 'active' : ''} onClick={() => setSolveType('full')}>解/改整张图片</button>
              <button className={solveType === 'specific' ? 'active' : ''} onClick={() => setSolveType('specific')}>指定题目</button>
            </div>
          
            {solveType === 'specific' && (
              <div className="specific-question-input">
                <input 
                  type="text"
                  placeholder="例如：请做第3题，或者带有「函数」字样的题目"
                  value={specificQuestion}
                  onChange={(e) => setSpecificQuestion(e.target.value)}
                />
              </div>
            )}
            <div className="upload-section">
              <h3>
                {imageSrc 
                  ? "已上传图片" 
                  : (mode === 'solve' ? "请上传题目图片" : "请上传包含题目与答案的图片")
                }
              </h3>
              {!imageSrc ? (
                 <div className="upload-box" onClick={() => fileInputRef.current?.click()}>
                    <input ref={fileInputRef} id="file-input" type="file" accept="image/*" onChange={onSelectFile} style={{ display: 'none' }} />
                    <span>+</span><p>选择文件</p>
                 </div>
              ) : (
                <div className="crop-container">
                  <p className='crop-instruction'>（可选）请拖动选框以选择特定区域</p>
                  <ReactCrop crop={crop} onChange={c => setCrop(c)}>
                    <img ref={imgRef} src={imageSrc} alt="Crop preview" />
                  </ReactCrop>
                </div>
              )}
            </div>
            
            {imageSrc && (
              <div className="main-action-button-container">
                <button onClick={() => handleInitialSend(fileRef.current!, imageSrc)} className="modern-button">
                  {mode === 'solve' ? '解析整张图片' : '批改整张图片'}
                </button>
                <button
                  onClick={handleCropAndSend}
                  className="modern-button"
                  style={{backgroundImage: 'linear-gradient(90deg, #6c757d 0%, #343a40 100%)'}}
                  disabled={!crop?.width || !crop?.height}
                >
                  仅处理裁剪区域
                </button>
              </div>
            )}
          </div>
        ) : (
          <>
          <div className="chat-container card-container">
            {/* 题目图片回显 */}
            {chatImageSrc && (
              <div className="solved-image-container chat-image-display">
                <h3>题目原文</h3>
                <img src={chatImageSrc} alt="当前处理的题目" className="solved-image" />
              </div>
            )}
            <div className="chat-messages">
              {(() => {
                console.log('🎨 [渲染] 开始渲染消息列表, 总数:', messages.length);
                
                // 过滤无效消息
                const validMessages = messages.filter(msg => {
                  const isValid = msg && msg.content && typeof msg.content === 'string';
                  if (!isValid) {
                    console.warn('⚠️ [渲染] 跳过无效消息:', msg);
                  }
                  return isValid;
                });
                
                console.log('✅ [渲染] 有效消息数:', validMessages.length);
                
                return validMessages.map((msg, index) => {
                  console.log(`🔹 [渲染] 第${index + 1}条消息, role: ${msg.role}, 长度: ${msg.content?.length || 0}`);
                  
                  // 安全地解析Markdown
                  let htmlContent = '';
                  try {
                    const contentToRender = msg.content || '';
                    htmlContent = marked.parse(contentToRender) as string;
                    console.log(`  ✅ [Markdown] 解析成功`);
                  } catch (err) {
                    console.error(`  ❌ [Markdown] 解析失败:`, err);
                    htmlContent = (msg.content || '').replace(/\n/g, '<br/>');
                  }
                  
                  try {
                    return (
                      <div key={index} className={`message-bubble-wrapper ${msg.role}`}>
                        {msg.role === 'user' && <div className="avatar user-avatar">You</div>}
                        <div className={`message-bubble ${msg.role}`}>
                          <div className="message-content" dangerouslySetInnerHTML={{ __html: htmlContent }}></div>
                        </div>
                        {msg.role === 'assistant' && <div className="avatar assistant-avatar">AI</div>}
                      </div>
                    );
                  } catch (renderErr) {
                    console.error(`  ❌ [渲染] JSX渲染失败:`, renderErr);
                    return (
                      <div key={index} className="message-bubble-wrapper assistant">
                        <div className="message-bubble assistant" style={{ backgroundColor: '#fff3cd', border: '1px solid #ffc107' }}>
                          <p>⚠️ 此消息渲染失败</p>
                        </div>
                      </div>
                    );
                  }
                });
              })()}
              {isLoading && (
                <div className="message-bubble-wrapper assistant">
                  <div className="message-bubble assistant">
                    {statusText ? (
                      <div className="ai-thinking-indicator">
                        <span>{statusText}</span>
                        <div className="loading-dots">
                          <span></span><span></span><span></span>
                        </div>
                      </div>
                    ) : (
                      <div className="typing-indicator">
                        <span></span><span></span><span></span>
                      </div>
                    )}
                  </div>
                </div>
              )}
              <div ref={chatEndRef}></div>
            </div>
            {/* 只有在有回答后才显示输入框 */}
            {messages.length > 0 && !isLoading && (
              <>
                {/* 快捷按钮 */}
                {showQuickButtons && (
                  <div className="quick-buttons-container">
                    <button 
                      className="quick-button quick-button-continue"
                      onClick={() => handleQuickButtonClick('请继续回答')}
                    >
                      <span className="quick-button-icon">💬</span>
                      <span>请继续回答</span>
                    </button>
                    <button 
                      className="quick-button quick-button-check"
                      onClick={() => handleQuickButtonClick('请检查回答是否有误')}
                    >
                      <span className="quick-button-icon">🔍</span>
                      <span>请检查回答是否有误</span>
                    </button>
                  </div>
                )}
                
                <div className="chat-input-area">
                  <textarea
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder="针对以上内容继续提问..."
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        if(userInput.trim()) sendMessage(userInput);
                      }
                    }}
                  />
                  <button onClick={() => {if(userInput.trim()) sendMessage(userInput)}} disabled={!userInput.trim()}>
                    发送
                  </button>
                </div>
              </>
            )}
          </div>
          </>
        )}
      </main>
    </div>
  );
}

// --- 顶层App组件（添加登录状态管理）---
function AppCore() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userId, setUserId] = useState('');
  const [token, setToken] = useState('');
  const [mode, setMode] = useState<'solve' | 'review' | 'mistakeBook' | null>(null);

  // 检查本地存储的登录状态
  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    const savedUserId = localStorage.getItem('userId');
    if (savedToken && savedUserId) {
      setToken(savedToken);
      setUserId(savedUserId);
      setIsLoggedIn(true);
    }
  }, []);

  const handleLoginSuccess = (uid: string, tok: string) => {
    setUserId(uid);
    setToken(tok);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    setIsLoggedIn(false);
    setUserId('');
    setToken('');
    setMode(null);
  };

  const handleBackToModeSelection = () => {
    console.log('🔙 [App] 返回模式选择');
    setMode(null);
  };

  // 如果未登录，显示登录界面
  if (!isLoggedIn) {
    return <AuthScreen onLoginSuccess={handleLoginSuccess} />;
  }

  // 如果已登录但未选择模式，显示模式选择器
  if (!mode) {
    console.log('🎯 [App] 显示模式选择器');
    return <ModeSelector onSelectMode={setMode} onLogout={handleLogout} />;
  }

  // 显示主应用
  console.log('🎯 [App] 当前模式:', mode);
  return <MainApp mode={mode} onBack={handleBackToModeSelection} userId={userId} token={token} onLogout={handleLogout} />;
}

// 用ErrorBoundary包裹整个App
function AppDB() {
  return (
    <ErrorBoundary>
      <AppCore />
    </ErrorBoundary>
  );
}

export default AppDB;
