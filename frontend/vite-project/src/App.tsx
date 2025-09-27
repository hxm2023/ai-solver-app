// ==============================================================================
// 完整 App.tsx - 【V21.0 终极对话完整版】
// ==============================================================================

import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
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
interface MainAppProps {
  mode: 'solve' | 'review';
  onBack: () => void;
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
  const [sessionId, setSessionId] = useState<string | null>(localStorage.getItem(`sessionId_${mode}`));
  const [chatTitle, setChatTitle] = useState<string>(localStorage.getItem(`chatTitle_${mode}`) || "新对话");
  const [userInput, setUserInput] = useState<string>('');
  const [solveType, setSolveType] = useState<'single' | 'full' | 'specific'>('single');
  const [specificQuestion, setSpecificQuestion] = useState<string>('');

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [statusText, setStatusText] = useState<string>('');
  
  const [imageSrc, setImageSrc] = useState<string>('');
  const [crop, setCrop] = useState<Crop>();
  const [isUploading, setIsUploading] = useState<boolean>(!sessionId); // 如果有会话记录，直接进入聊天
  
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
          window.MathJax.typesetPromise(Array.from(answerDivs)).catch((err) => console.error('MathJax typeset error:', err));
        }
      }, 100);
    }
  }, [messages]);
  
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    if (sessionId) {
      localStorage.setItem(`sessionId_${mode}`, sessionId);
      localStorage.setItem(`chatTitle_${mode}`, chatTitle);
    } else {
      localStorage.removeItem(`sessionId_${mode}`);
      localStorage.removeItem(`chatTitle_${mode}`);
    }
  }, [sessionId, chatTitle, mode]);

  // --- 核心逻辑函数 ---
  const sendMessage = async (prompt: string, imageBlob?: Blob | File) => {
    setIsLoading(true);
    setError('');
    
    // 乐观更新UI
    if (!imageBlob) {
      setMessages(prev => [...prev, { role: 'user', content: prompt }]);
    }
    setUserInput('');

    let currentSessionId = sessionId;
    let currentAssistantResponse = '';
    let isTruncated = true;

    while (isTruncated) {
      try {
        let imageBase64: string | undefined = undefined;
        if (imageBlob && currentAssistantResponse === '') {
          imageBase64 = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
            reader.onerror = reject;
            reader.readAsDataURL(imageBlob);
          });
        }

        const response = await axios.post<any>(`${backendUrl}/chat`, {
          session_id: currentSessionId,
          prompt: currentAssistantResponse === '' ? prompt : "请接着你刚才说的继续。",
          image_base_64: imageBase64,
        });

        const data = response.data;
        
        if (!currentSessionId) {
          currentSessionId = data.session_id;
          setSessionId(data.session_id);
          if (data.title && data.title !== "新对话") setChatTitle(data.title);
        }

        currentAssistantResponse += data.response;
        isTruncated = data.is_truncated;
        
        const userMessage = { role: 'user' as const, content: prompt };
        const assistantMessage = { role: 'assistant' as const, content: currentAssistantResponse };
        
        if (!imageBlob) {
            setMessages(prev => [...prev.slice(0, -1), userMessage, assistantMessage]);
        } else {
            setMessages([userMessage, assistantMessage]);
        }
        
        if (isTruncated) {
          setStatusText("答案稍长，正在加载后续回答...");
        } else {
          setStatusText('');
        }

      } catch (err) {
        let detail = "未知错误";
        if (axios.isAxiosError(err) && err.response) {
          detail = err.response.data.detail || err.message;
        } else if (err instanceof Error) {
          detail = err.message;
        }
        setError(`糟糕，出错了！错误详情: ${detail}`);
        console.error("请求错误:", err);
        if (!imageBlob) {
          setMessages(prev => prev.slice(0, -1));
        }
        isTruncated = false;
      }
    }
    
    setIsLoading(false);
  };

  const handleInitialSend = (imageBlob: Blob | File, imageSrcForDisplay: string) => {
      let promptText = '';
      // 根据模式和solveType，动态生成初始prompt
      if (solveType === 'single') {
        promptText = mode === 'solve' ? '请详细解答这道题目。' : '请详细批改这张同时包含题目和答案的图片。';
      } else if (solveType === 'full') {
        promptText = mode === 'solve' ? '请详细解答这张图片中的所有题目。' : '请详细批改这张图片中的所有题目。';
      } else { // specific
        if (!specificQuestion) { setError('请输入你要指定的题目信息。'); return; }
        const basePrompt = mode === 'solve' ? '请详细解答这道题目(不要考察别的题目)：' : '请详细批改这道题目(不要考察别的题目)：';
        promptText = `${basePrompt} ${specificQuestion}`;
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
        handleInitialSend(blob, croppedImageSrc); // <<< 现在传递了两个参数！
      }
    }, 'image/png');
  };
// ==============================================================================
// 完整 App.tsx - 第三部分: UI渲染 (JSX)
// ==============================================================================
  return (
    <div className="App">
      <header className="App-header">
        <h1>{isUploading ? (mode === 'solve' ? 'AI 智能解题' : 'AI 批改作业') : chatTitle}</h1>
        <button onClick={onBack} className="back-button">返回</button>
      </header>
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
                      <div className="status-text-inline">{statusText}</div>
                    ) : (
                      <div className="typing-indicator">
                        <span></span><span></span><span></span>
                      </div>
                    )}
                  </div>
                </div>
              )}
              {/* 我们不再需要手动的“继续回答”按钮了！ */}
              <div ref={chatEndRef}></div>
            </div>
            {/* --- 【核心修改】: 只有在有回答后才显示输入框 --- */}
            {messages.length > 0 && !isLoading && (
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