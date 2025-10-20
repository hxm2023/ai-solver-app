// ==============================================================================
// 完整 App.tsx - 【V22.0 追问图片记忆修复版 + V19.0混合输入架构】
// 后端：OCR增强（Pix2Text）+ 原图视觉（通义千问） + 追问带图片
// 前端：手动续答逻辑
// 核心修复：追问时后端重新发送图片，避免AI遗忘或幻觉
// ==============================================================================

import React, { useState, useRef, useEffect } from 'react';
import { marked } from 'marked';
import './App.css';
import './ModeSelector.css';

import ReactCrop, { type Crop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import SimpleMistakeBook from './SimpleMistakeBook';

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
  messages?: Message[];  // 保存完整消息历史
  // 不再保存 imageBase64（避免 localStorage 配额超出）
};

interface MainAppProps {
  mode: 'solve' | 'review' | 'mistakeBook';
  onBack: () => void;
}

// --- 会话管理工具函数 ---
const SESSION_STORAGE_KEY = 'ai_solver_sessions';

function getSessions(): SessionInfo[] {
  try {
    const data = localStorage.getItem(SESSION_STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
}

function saveSession(session: SessionInfo) {
  const sessions = getSessions();
  const existingIndex = sessions.findIndex(s => s.sessionId === session.sessionId);
  
  if (existingIndex >= 0) {
    // 更新现有会话
    sessions[existingIndex] = { ...sessions[existingIndex], ...session };
  } else {
    // 添加新会话（放在最前面）
    sessions.unshift(session);
  }
  
  // 只保留最近50个会话
  const limitedSessions = sessions.slice(0, 50);
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(limitedSessions));
}

function deleteSession(sessionId: string) {
  const sessions = getSessions().filter(s => s.sessionId !== sessionId);
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessions));
}

// --- 模式选择器组件 ---
interface ModeSelectorProps {
  onSelectMode: (mode: 'solve' | 'review' | 'mistakeBook') => void;
}
const ModeSelector: React.FC<ModeSelectorProps> = ({ onSelectMode }) => {
  return (
    <div className="mode-selector-container">
      <div className="mode-selector-card">
        <h1 className="mode-selector-title">请选择功能模式</h1>
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
// 完整 App.tsx - 第二部分: MainApp组件
// ==============================================================================

function MainApp({ mode, onBack }: MainAppProps) {
  // 如果是错题本模式，直接渲染SimpleMistakeBook
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
          <div style={{ width: '100px' }}></div>
        </div>
        <SimpleMistakeBook />
      </div>
    );
  }
  // --- 状态管理 ---
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
  const [showQuickButtons, setShowQuickButtons] = useState<boolean>(false); // 控制快捷按钮显示
  
  const [imageSrc, setImageSrc] = useState<string>('');
  const [crop, setCrop] = useState<Crop>();
  const [isUploading, setIsUploading] = useState<boolean>(true); // 默认显示上传界面
  
  // --- 【新增】侧边栏相关状态 ---
  const [showSidebar, setShowSidebar] = useState<boolean>(false);
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  
  const imgRef = useRef<HTMLImageElement | null>(null);
  const fileRef = useRef<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const backendUrl = 'http://127.0.0.1:8000';

  // --- 【统一】MathJax渲染 & 滚动 ---
  useEffect(() => {
    console.log('🔄 [useEffect] messages更新, 数量:', messages.length);
    
    if (messages.length > 0) {
      const timer = setTimeout(() => {
        try {
          console.log('📐 [MathJax] 准备渲染...');
          
          // 滚动到底部
          if (chatEndRef.current) {
            chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
            console.log('✅ [Scroll] 已滚动到底部');
          }
          
          // MathJax渲染
          if (window.MathJax && window.MathJax.typesetPromise) {
            window.MathJax.typesetPromise()
              .then(() => {
                console.log('✅ [MathJax] 渲染成功');
              })
              .catch((err: any) => {
                console.error('❌ [MathJax] 渲染失败:', err);
                console.error('❌ [MathJax] 错误堆栈:', err.stack);
              });
          } else {
            console.warn('⚠️ [MathJax] MathJax未加载或不可用');
          }
        } catch (err) {
          console.error('❌ [useEffect] MathJax渲染流程异常:', err);
        }
      }, 150);
      
      return () => {
        console.log('🧹 [useEffect] 清理定时器');
        clearTimeout(timer);
      };
    }
  }, [messages, isLoading]);

  // --- 【新增】加载会话列表 ---
  useEffect(() => {
    console.log('📋 [useEffect] 加载会话列表, mode:', mode);
    try {
      const allSessions = getSessions().filter(s => s.mode === mode);
      setSessions(allSessions);
      console.log('✅ [会话列表] 加载成功, 数量:', allSessions.length);
    } catch (err) {
      console.error('❌ [会话列表] 加载失败:', err);
    }
  }, [mode]);
  
  // --- 【新增】保存当前会话到历史（包含完整消息） ---
  useEffect(() => {
    if (sessionId && chatTitle && chatImageSrc && messages.length > 0) {
      console.log('💾 [useEffect] 保存会话, sessionId:', sessionId);
      try {
        saveSession({
          sessionId,
          title: chatTitle,
          timestamp: Date.now(),
          mode,
          imageSrc: chatImageSrc,
          messages: messages
        });
        // 刷新会话列表
        setSessions(getSessions().filter(s => s.mode === mode));
        console.log('✅ [会话保存] 成功');
      } catch (err) {
        console.error('❌ [会话保存] 失败:', err);
      }
    }
  }, [sessionId, chatTitle, chatImageSrc, messages, mode]);

  // --- 核心逻辑函数 (流式版本) ---
  const sendMessage = async (prompt: string, imageBlob?: Blob | File) => {
    console.log('[sendMessage] 开始, imageBlob存在:', !!imageBlob);
    
    setIsLoading(true);
    setError('');
    setShowQuickButtons(false); // 发送消息时隐藏快捷按钮
    setStatusText('正在连接AI...');
    
    // 记录是否是第一次发送（有图片的情况）
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
        console.log('[sendMessage] Base64长度:', imageBase64?.length);
      } else {
        console.log('[sendMessage] 没有图片数据');
      }

      // 构建请求体
      const requestBody = {
        session_id: currentSessionId,
        prompt: prompt,
        image_base_64: imageBase64,
      };

      console.log('[sendMessage] 请求体构建完成:');
      console.log('  - session_id:', currentSessionId || '(新会话)');
      console.log('  - prompt长度:', prompt.length);
      console.log('  - has_image:', !!imageBase64);
      console.log('[sendMessage] 发起流式请求...');
      
      // 【临时测试】先使用非流式接口确认图片传递是否正常
      // TODO: 测试成功后改回 /chat_stream
      console.log('[临时] 使用非流式接口 /chat 进行测试...');
      const response = await fetch(`${backendUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      // 【临时】非流式接口处理
      const data = await response.json();
      
      console.log('[DEBUG] ========== 收到后端响应 ==========');
      console.log('[DEBUG] response.ok:', response.ok);
      console.log('[DEBUG] response.status:', response.status);
      console.log('[DEBUG] data:', data);
      console.log('[DEBUG] data.session_id:', data.session_id);
      console.log('[DEBUG] data.response 长度:', data.response?.length);
      console.log('[DEBUG] data.error:', data.error);
      console.log('[DEBUG] =====================================');
      
      // 检查HTTP错误
      if (!response.ok) {
        // 特殊处理404（会话失效）
        if (response.status === 404) {
          throw new Error(`404: ${data.detail || '会话已失效'}`);
        }
        throw new Error(`HTTP error! status: ${response.status}, ${data.detail || ''}`);
      }
      console.log('[临时] 收到非流式响应:', data);
      
      // 处理session_id
      if (data.session_id && !currentSessionId) {
        currentSessionId = data.session_id;
        setSessionId(data.session_id);
        if (data.title) setChatTitle(data.title);
        
        // 【修复】不再保存图片到localStorage（避免超出配额）
        // 后端已存储图片，如果后端重启会话丢失，提示用户重新开始即可
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
          // 清理特殊标记
          fullContent = fullContent.replace("[MISTAKE_DETECTED]", "").replace("[CORRECT]", "").trim();
        }
        
        console.log('📦 [消息更新] ========== 准备更新消息 ==========');
        console.log('📦 [消息更新] fullContent 长度:', fullContent?.length);
        console.log('📦 [消息更新] fullContent 类型:', typeof fullContent);
        console.log('📦 [消息更新] fullContent 前100字:', fullContent?.substring(0, 100));
        console.log('📦 [消息更新] imageBlob 存在:', !!imageBlob);
        console.log('📦 [消息更新] 当前 messages 数量:', messages.length);
        console.log('📦 [消息更新] mistake_saved:', data.mistake_saved);
        console.log('📦 [消息更新] ================================================');
        
        try {
          if (!imageBlob) {
            console.log('📝 [消息更新] 追问模式 - 追加AI回答');
            setMessages(prev => {
              console.log('  📝 [状态更新] 当前消息数:', prev.length);
              const newMessages = [...prev, { role: 'assistant' as const, content: fullContent }];
              console.log('  📝 [状态更新] 更新后消息数:', newMessages.length);
              console.log('  📝 [状态更新] 最后一条消息长度:', newMessages[newMessages.length - 1]?.content?.length);
              return newMessages;
            });
            console.log('✅ [消息更新] 追问模式消息更新完成');
          } else {
            console.log('📝 [消息更新] 首次提问 - 创建新消息列表');
            const newMessages: Message[] = [
              userMessage, 
              { role: 'assistant' as const, content: fullContent }
            ];
            console.log('  📝 [状态更新] 新消息列表长度:', newMessages.length);
            console.log('  📝 [状态更新] 用户消息:', userMessage.content.substring(0, 50));
            console.log('  📝 [状态更新] AI消息长度:', fullContent.length);
            
            setMessages(newMessages);
            console.log('✅ [消息更新] 首次提问消息更新完成');
          }
        } catch (updateErr) {
          console.error('❌ [消息更新] setMessages调用失败:', updateErr);
          console.error('❌ [消息更新] 错误详情:', {
            name: (updateErr as Error).name,
            message: (updateErr as Error).message,
            stack: (updateErr as Error).stack
          });
          throw updateErr; // 重新抛出，让外层catch处理
        }
      }

    } catch (err) {
      hasError = true;
      let detail = "未知错误";
      
      // 检查是否是会话失效错误（404）
      if (err instanceof Error && err.message.includes('404')) {
        console.log('[错误] 会话已失效，后端可能重启了');
        setError(`会话已失效（可能是服务重启），请点击右上角"新对话"按钮重新开始`);
        // 清空session相关状态
        setSessionId(null);
        setChatTitle("新对话");
        
        // 3秒后自动跳转到上传界面
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
    
    // 第一次AI回答后显示快捷按钮（只有成功时才显示）
    if (isFirstMessage && !hasError) {
      console.log('✅ 第一次回答完成，显示快捷按钮');
      setShowQuickButtons(true);
    } else {
      console.log('[sendMessage] 不显示按钮 - isFirstMessage:', isFirstMessage, 'hasError:', hasError);
    }
  };

  // 快捷按钮处理函数
  const handleQuickButtonClick = (message: string) => {
    sendMessage(message);
  };

  const handleInitialSend = (imageBlob: Blob | File, imageSrcForDisplay: string) => {
      console.log('[DEBUG] ========== handleInitialSend 调用 ==========');
      console.log('[DEBUG] imageBlob:', imageBlob);
      console.log('[DEBUG] imageSrcForDisplay 长度:', imageSrcForDisplay?.length);
      
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
      
      console.log('[DEBUG] promptText:', promptText);
      console.log('[DEBUG] 设置 chatImageSrc...');
      setChatImageSrc(imageSrcForDisplay);
      console.log('[DEBUG] 设置 isUploading = false...');
      setIsUploading(false); // 切换到聊天界面
      console.log('[DEBUG] 调用 sendMessage...');
      sendMessage(promptText, imageBlob);
      console.log('[DEBUG] =====================================');
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
  
  // --- 【新增】会话管理处理函数 ---
  const handleLoadSession = async (session: SessionInfo) => {
    console.log('[会话恢复] 开始加载会话:', session.sessionId);
    
    // 【修复】验证并清理消息数据，确保格式正确
    const validMessages = (session.messages || []).filter((msg): msg is Message => {
      // 确保msg存在，有role和content字段
      return msg && 
             typeof msg === 'object' && 
             (msg.role === 'user' || msg.role === 'assistant') && 
             typeof msg.content === 'string';
    });
    
    console.log('[会话恢复] 原始消息数:', session.messages?.length || 0);
    console.log('[会话恢复] 有效消息数:', validMessages.length);
    
    // 恢复前端状态
    setSessionId(session.sessionId);
    setChatTitle(session.title);
    setChatImageSrc(session.imageSrc || '');
    setIsUploading(false);
    setMessages(validMessages); // 使用验证后的消息
    setShowSidebar(false);
    
    console.log('[会话提示] 如需继续追问，请确保后端服务未重启（会话仍在内存中）');
    
    // 【简化】不再尝试恢复后端会话
    // 如果后端重启导致会话丢失，用户追问时会收到404错误提示，引导重新开始
  };
  
  const handleDeleteSession = (sessionIdToDelete: string) => {
    deleteSession(sessionIdToDelete);
    setSessions(getSessions().filter(s => s.mode === mode));
    
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
// 完整 App.tsx - 第三部分: UI渲染 (JSX)
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
        </div>
      </header>
      
      {/* --- 【新增】侧边栏 --- */}
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
                  placeholder="例如：请做第3题，或者带有“函数”字样的题目"
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
            {(() => {
              console.log('[DEBUG] ========== 渲染聊天界面 ==========');
              console.log('[DEBUG] isUploading:', isUploading);
              console.log('[DEBUG] messages 数量:', messages.length);
              console.log('[DEBUG] chatImageSrc 存在:', !!chatImageSrc);
              console.log('[DEBUG] messages:', messages);
              console.log('[DEBUG] =======================================');
              return null;
            })()}
          <div className="chat-container card-container">
            {/* --- 【新增】题目图片回显 --- */}
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
                  console.log(`🔹 [渲染] 第${index + 1}/${validMessages.length}条消息, role: ${msg.role}, 长度: ${msg.content?.length || 0}`);
                  
                  // 安全地解析Markdown，添加容错处理
                  let htmlContent = '';
                  try {
                    const contentToRender = msg.content || '';
                    console.log(`  📝 [Markdown] 准备解析, 前50字: ${contentToRender.substring(0, 50)}...`);
                    
                    htmlContent = marked.parse(contentToRender) as string;
                    
                    console.log(`  ✅ [Markdown] 解析成功, HTML长度: ${htmlContent.length}`);
                  } catch (err) {
                    console.error(`  ❌ [Markdown] 解析失败 (消息${index + 1}):`, err);
                    console.error(`  ❌ [Markdown] 错误详情:`, {
                      message: (err as Error).message,
                      stack: (err as Error).stack,
                      content: msg.content?.substring(0, 100)
                    });
                    
                    // 如果解析失败，使用原始文本
                    htmlContent = (msg.content || '').replace(/\n/g, '<br/>');
                    console.log(`  🔄 [Markdown] 降级为纯文本, 长度: ${htmlContent.length}`);
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
                    console.error(`  ❌ [渲染] JSX渲染失败 (消息${index + 1}):`, renderErr);
                    // 返回错误占位符
                    return (
                      <div key={index} className="message-bubble-wrapper assistant">
                        <div className="message-bubble assistant" style={{ backgroundColor: '#fff3cd', border: '1px solid #ffc107' }}>
                          <p>⚠️ 此消息渲染失败</p>
                          <details>
                            <summary>查看原始内容</summary>
                            <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                              {msg.content?.substring(0, 500)}
                            </pre>
                          </details>
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
              {/* 我们不再需要手动的"继续回答"按钮了！ */}
              <div ref={chatEndRef}></div>
            </div>
            {/* --- 【核心修改】: 只有在有回答后才显示输入框 --- */}
            {messages.length > 0 && !isLoading && (
              <>
                {/* 调试信息 */}
                {console.log('[UI渲染] showQuickButtons:', showQuickButtons, 'messages.length:', messages.length, 'isLoading:', isLoading)}
                
                {/* --- 【新增】快捷按钮 --- */}
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

// --- 顶层App组件 (负责模式切换和重置) ---
function AppCore() {
  const [mode, setMode] = useState<'solve' | 'review' | 'mistakeBook' | null>(null);

  const handleBackToModeSelection = () => {
    console.log('🔙 [App] 返回模式选择');
    // 返回时，清除所有模式的会话记录
    localStorage.removeItem('sessionId_solve');
    localStorage.removeItem('chatTitle_solve');
    localStorage.removeItem('sessionId_review');
    localStorage.removeItem('chatTitle_review');
    setMode(null);
  };
  
  if (!mode) {
    console.log('🎯 [App] 显示模式选择器');
    return <ModeSelector onSelectMode={setMode} />;
  }

  console.log('🎯 [App] 当前模式:', mode);
  return <MainApp mode={mode} onBack={handleBackToModeSelection} />;
}

// 用ErrorBoundary包裹整个App
function App() {
  return (
    <ErrorBoundary>
      <AppCore />
    </ErrorBoundary>
  );
}

export default App;