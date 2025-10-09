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

// 声明全局MathJax对象
declare global {
  interface Window { MathJax: any; }
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
};

interface MainAppProps {
  mode: 'solve' | 'review';
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
  onSelectMode: (mode: 'solve' | 'review') => void;
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
        </div>
      </div>
    </div>
  );
};
// ==============================================================================
// 完整 App.tsx - 第二部分: MainApp组件
// ==============================================================================

function MainApp({ mode, onBack }: MainAppProps) {
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

  // --- 效果钩子 (渲染 & 滚动 & 会话持久化) ---
  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        const answerDivs = document.querySelectorAll('.message-content');
        if (answerDivs.length > 0 && window.MathJax?.typesetPromise) {
          window.MathJax.typesetPromise(Array.from(answerDivs)).catch((err: any) => console.error('MathJax typeset error:', err));
        }
      }, 100);
    }
  }, [messages]);
  
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // --- 【新增】加载会话列表 ---
  useEffect(() => {
    const allSessions = getSessions().filter(s => s.mode === mode);
    setSessions(allSessions);
  }, [mode]);
  
  // --- 【新增】保存当前会话到历史 ---
  useEffect(() => {
    if (sessionId && chatTitle && chatImageSrc) {
      saveSession({
        sessionId,
        title: chatTitle,
        timestamp: Date.now(),
        mode,
        imageSrc: chatImageSrc
      });
      // 刷新会话列表
      setSessions(getSessions().filter(s => s.mode === mode));
    }
  }, [sessionId, chatTitle, chatImageSrc, mode]);

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
      }
      
      // 处理错误
      if (data.error) {
        setError(`错误: ${data.error}`);
        hasError = true;
      } else {
        // 显示完整回答
        const fullContent = data.response;
        
        if (!imageBlob) {
          setMessages(prev => [...prev, { role: 'assistant', content: fullContent }]);
        } else {
          setMessages([userMessage, { role: 'assistant', content: fullContent }]);
        }
        
        console.log('[临时] AI回答长度:', fullContent.length);
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
      sendMessage(promptText, imageBlob);
      setIsUploading(false); // 切换到聊天界面
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
  const handleLoadSession = (session: SessionInfo) => {
    // 注意：这里我们只加载会话元数据，实际的消息历史在后端
    setSessionId(session.sessionId);
    setChatTitle(session.title);
    setChatImageSrc(session.imageSrc || '');
    setIsUploading(false);
    setMessages([]); // 清空消息，因为后端会重建历史
    setShowSidebar(false);
    
    // TODO: 如果需要，可以添加一个API来获取完整的历史记录
    console.log('切换到会话:', session.sessionId);
  };
  
  const handleDeleteSession = (sessionIdToDelete: string) => {
    deleteSession(sessionIdToDelete);
    setSessions(getSessions().filter(s => s.mode === mode));
    
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
          <div className="chat-container card-container">
            {/* --- 【新增】题目图片回显 --- */}
            {chatImageSrc && (
              <div className="solved-image-container chat-image-display">
                <h3>题目原文</h3>
                <img src={chatImageSrc} alt="当前处理的题目" className="solved-image" />
              </div>
            )}
            <div className="chat-messages">
              {messages.map((msg, index) => (
                <div key={index} className={`message-bubble-wrapper ${msg.role}`}>
                  {/* --- 【新增】用户头像 (可选美化) --- */}
                  {msg.role === 'user' && <div className="avatar user-avatar">You</div>}
                  <div className={`message-bubble ${msg.role}`}>
                    <div className="message-content" dangerouslySetInnerHTML={{ __html: marked.parse(msg.content) }}></div>
                  </div>
                  {msg.role === 'assistant' && <div className="avatar assistant-avatar">AI</div>}
                </div>
              ))}
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
        )}
      </main>
    </div>
  );
}

// --- 顶层App组件 (负责模式切换和重置) ---
function App() {
  const [mode, setMode] = useState<'solve' | 'review' | null>(null);

  const handleBackToModeSelection = () => {
    // 返回时，清除所有模式的会话记录
    localStorage.removeItem('sessionId_solve');
    localStorage.removeItem('chatTitle_solve');
    localStorage.removeItem('sessionId_review');
    localStorage.removeItem('chatTitle_review');
    setMode(null);
  };
  
  if (!mode) {
    return <ModeSelector onSelectMode={setMode} />;
  }

  return <MainApp mode={mode} onBack={handleBackToModeSelection} />;
}

export default App;