// ==============================================================================
// 完整 App.tsx - 【V24.0 整页多题并行处理版】
// 后端：题目自动分割 + OCR增强 + 原图视觉（通义千问）
// 前端：多会话并行管理 + 分页Tab界面 + 快捷按钮
// 核心升级：
// - V24.0: 整页多题智能分割、并行处理、Tab式切换界面
// - V23.0: 高级图像增强（锐化+CLAHE）、AI智能校正、图片质量检测
// - V22.0: 追问时后端重新发送图片，避免AI遗忘或幻觉
// ==============================================================================

import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { marked } from 'marked';
import './App.css';
import './ModeSelector.css';

import ReactCrop, { type Crop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';

// V24.0 新增: 导入题目选择器组件
import QuestionSelector from './QuestionSelector';

// 声明全局MathJax对象
declare global {
  interface Window { MathJax: any; }
}

// --- 类型定义 ---
type Message = {
  role: 'user' | 'assistant';
  content: string;
};

// V24.0 新增: 单个聊天会话的数据结构
type ChatSession = {
  id: string;                  // 题目单元唯一ID
  imageSrc: string;            // 裁剪后的题目图片（带data:image前缀）
  sessionId: string | null;    // 此题目专属的后端聊天会话ID
  messages: Message[];         // 聊天消息历史
  isLoading: boolean;          // 加载状态
  error: string;               // 错误信息
  statusText: string;          // 状态文本
  showQuickButtons: boolean;   // 是否显示快捷按钮
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
  // --- V24.0 状态管理大修：多会话架构 ---
  const [sessions, setSessions] = useState<ChatSession[]>([]);  // 多会话数组
  const [activeSessionIndex, setActiveSessionIndex] = useState<number>(0);  // 当前激活的会话索引
  const [isProcessingSheet, setIsProcessingSheet] = useState<boolean>(false);  // 整页分割处理中
  
  // 保留的全局状态
  const [chatTitle, setChatTitle] = useState<string>("新对话");
  const [userInput, setUserInput] = useState<string>('');
  const [solveType, setSolveType] = useState<'single' | 'full' | 'specific'>('single');
  const [specificQuestion, setSpecificQuestion] = useState<string>('');
  const [error, setError] = useState<string>('');  // 全局错误
  const [statusText, setStatusText] = useState<string>('');  // 全局状态文本
  
  // 图片上传相关状态（用于初始上传界面）
  const [imageSrc, setImageSrc] = useState<string>('');
  const [crop, setCrop] = useState<Crop>();
  const [isUploading, setIsUploading] = useState<boolean>(true);  // V24.0: 默认显示上传界面
  
  const imgRef = useRef<HTMLImageElement | null>(null);
  const fileRef = useRef<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const backendUrl = 'http://127.0.0.1:8000';

  // --- V23.0新增：图片质量检测函数 ---
  const checkImageQuality = (file: File) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new window.Image();
      img.onload = () => {
        console.log(`[图片质量检测] 尺寸: ${img.naturalWidth}x${img.naturalHeight}`);
        
        // 检查1: 尺寸过小
        if (img.naturalWidth < 300 || img.naturalHeight < 300) {
          setError("⚠️ 图片尺寸过小，可能无法清晰识别。建议使用更高分辨率的图片（至少300x300像素）。");
          return;
        }
        
        // 检查2: 尺寸过大（超过4K可能导致处理缓慢）
        if (img.naturalWidth > 3840 || img.naturalHeight > 2160) {
          console.warn("[图片质量检测] 图片尺寸较大，处理可能需要更长时间");
          // 只警告，不阻止
        }
        
        // 检查3: 文件大小
        if (file.size > 10 * 1024 * 1024) {  // 10MB
          setError("⚠️ 图片文件过大（超过10MB）。建议压缩后再上传，以提升处理速度。");
          return;
        }
        
        // TODO: 可以添加更复杂的模糊度检测
        // 需要使用canvas来分析像素数据，计算梯度/方差等指标
        
        console.log("[图片质量检测] ✓ 质量检查通过");
      };
      img.src = event.target?.result as string;
    };
    reader.readAsDataURL(file);
  };

  // --- V24.0 效果钩子 (渲染 & 滚动) ---
  useEffect(() => {
    // MathJax渲染：监听sessions变化
    if (sessions.length > 0 && sessions[activeSessionIndex]?.messages.length > 0) {
      setTimeout(() => {
        const answerDivs = document.querySelectorAll('.message-content');
        if (answerDivs.length > 0 && window.MathJax?.typesetPromise) {
          window.MathJax.typesetPromise(Array.from(answerDivs)).catch((err: any) => console.error('MathJax typeset error:', err));
        }
      }, 100);
    }
  }, [sessions, activeSessionIndex]);
  
  useEffect(() => {
    // 自动滚动到底部
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sessions, activeSessionIndex]);

  // --- V24.0 核心逻辑函数：多会话版sendMessage ---
  const sendMessage = async (
    prompt: string, 
    sessionIndex: number, 
    imageBase64?: string, 
    hideButtons: boolean = true
  ) => {
    console.log(`[sendMessage] 会话 ${sessionIndex} 开始处理，prompt: ${prompt.substring(0, 50)}...`);
    
    // 更新特定会话的状态：开始加载
    setSessions(prev => prev.map((s, i) => 
      i === sessionIndex 
        ? { ...s, isLoading: true, error: '', showQuickButtons: hideButtons ? false : s.showQuickButtons }
        : s
    ));
    
    // 乐观更新：如果不是续答，立即添加用户消息
    const isFirstMessage = imageBase64 !== undefined;
    if (!isFirstMessage && prompt !== "请接着你刚才说的继续。") {
      setSessions(prev => prev.map((s, i) => 
        i === sessionIndex 
          ? { ...s, messages: [...s.messages, { role: 'user', content: prompt }] }
          : s
      ));
      setUserInput('');
    }

    // 获取当前会话的sessionId
    let currentSessionId = sessions[sessionIndex]?.sessionId || null;
    let currentAssistantResponse = '';
    let isTruncated = true;

    while (isTruncated) {
      try {
        // 只在首次请求时发送图片
        const imageToSend = (imageBase64 && currentAssistantResponse === '') ? imageBase64 : undefined;
        
        const response = await axios.post<any>(`${backendUrl}/chat`, {
          session_id: currentSessionId,
          prompt: currentAssistantResponse === '' ? prompt : "请接着你刚才说的继续。",
          image_base_64: imageToSend,
        });

        const data = response.data;
        
        // 首次响应时保存sessionId
        if (!currentSessionId) {
          currentSessionId = data.session_id;
          setSessions(prev => prev.map((s, i) => 
            i === sessionIndex ? { ...s, sessionId: data.session_id } : s
          ));
          if (data.title && data.title !== "新对话") {
            setChatTitle(data.title);
          }
        }

        // 累积响应内容
        currentAssistantResponse += data.response;
        isTruncated = data.is_truncated;
        
        // 更新UI：显示累积的完整回答
        const userMessage = { role: 'user' as const, content: prompt };
        const assistantMessage = { role: 'assistant' as const, content: currentAssistantResponse };
        
        setSessions(prev => prev.map((s, i) => {
          if (i !== sessionIndex) return s;
          
          // 如果是首次消息，设置完整的消息数组
          if (isFirstMessage) {
            return {
              ...s,
              messages: [userMessage, assistantMessage],
              statusText: isTruncated ? "答案稍长，正在加载后续回答..." : "",
              showQuickButtons: !isTruncated && hideButtons
            };
          } else {
            // 追问：更新最后一条assistant消息
            const newMessages = [...s.messages];
            const lastIndex = newMessages.length - 1;
            if (newMessages[lastIndex]?.role === 'assistant') {
              newMessages[lastIndex] = assistantMessage;
            } else {
              newMessages.push(assistantMessage);
            }
            return {
              ...s,
              messages: newMessages,
              statusText: isTruncated ? "答案稍长，正在加载后续回答..." : "",
              showQuickButtons: !isTruncated && hideButtons
            };
          }
        }));

      } catch (err) {
        let detail = "未知错误";
        if (axios.isAxiosError(err) && err.response) {
          detail = err.response.data.detail || err.message;
        } else if (err instanceof Error) {
          detail = err.message;
        }
        
        const errorMsg = `糟糕，出错了！错误详情: ${detail}`;
        console.error(`[sendMessage] 会话 ${sessionIndex} 错误:`, err);
        
        // 更新错误状态
        setSessions(prev => prev.map((s, i) => 
          i === sessionIndex 
            ? { ...s, error: errorMsg, isLoading: false }
            : s
        ));
        
        // 回滚乐观更新
        if (!isFirstMessage) {
          setSessions(prev => prev.map((s, i) => 
            i === sessionIndex 
              ? { ...s, messages: s.messages.slice(0, -1) }
              : s
          ));
        }
        
        isTruncated = false;
      }
    }
    
    // 完成加载
    setSessions(prev => prev.map((s, i) => 
      i === sessionIndex ? { ...s, isLoading: false } : s
    ));
    
    console.log(`[sendMessage] 会话 ${sessionIndex} 处理完成`);
  };

  // --- V24.0 新增：整页多题处理函数 ---
  const startMultiQuestionProcessing = async (imageBlob: Blob | File, initialPrompt: string) => {
    console.log('[startMultiQuestionProcessing] 开始整页处理流程...');
    
    setIsUploading(false);  // 立即切换到聊天视图
    setIsProcessingSheet(true);  // 显示分割处理中的状态
    setStatusText('🔍 正在智能识别和分割题目，请稍候...');
    setError('');

    try {
      // 1. 将图片转换为Base64
      const imageBase64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(imageBlob);
      });

      console.log('[startMultiQuestionProcessing] 图片转换完成，调用后端分割API...');

      // 2. 调用后端的 /process_sheet 端点
      const response = await axios.post(`${backendUrl}/process_sheet`, {
        prompt: initialPrompt,
        image_base_64: imageBase64,
      });

      const { questions, total_count } = response.data;
      console.log(`[startMultiQuestionProcessing] 后端返回 ${total_count} 个题目单元`);

      // 3. 初始化所有会话的状态
      const initialSessions: ChatSession[] = questions.map((q: any, index: number) => ({
        id: q.id,
        imageSrc: `data:image/png;base64,${q.image_base_64}`,
        sessionId: null,
        messages: [],
        isLoading: true,  // 初始为加载状态
        error: '',
        statusText: `等待处理... (${index + 1}/${total_count})`,
        showQuickButtons: false,
      }));
      
      setSessions(initialSessions);
      setIsProcessingSheet(false);
      setStatusText('');
      
      console.log(`[startMultiQuestionProcessing] 初始化 ${initialSessions.length} 个会话，准备并行处理...`);

      // 4. 【核心】并行处理所有题目单元
      // 使用 Promise.allSettled 而不是 Promise.all，这样即使某个题目失败也不会影响其他题目
      const processingPromises = initialSessions.map((session, index) => 
        sendMessage(initialPrompt, index, session.imageSrc.split(',')[1])
          .catch(err => {
            console.error(`[startMultiQuestionProcessing] 题目 ${index + 1} 处理失败:`, err);
            // 错误已在 sendMessage 中处理，这里只需记录
          })
      );

      await Promise.allSettled(processingPromises);
      console.log('[startMultiQuestionProcessing] ✅ 所有题目处理完成！');

    } catch (err) {
      let detail = "未知错误";
      if (axios.isAxiosError(err) && err.response) {
        detail = err.response.data.detail || err.message;
      } else if (err instanceof Error) {
        detail = err.message;
      }
      
      const errorMsg = `整页处理失败: ${detail}`;
      console.error('[startMultiQuestionProcessing] 错误:', err);
      setError(errorMsg);
      setIsProcessingSheet(false);
      setIsUploading(true);  // 返回上传界面
    }
  };

  // --- V24.0 修改：handleInitialSend 作为触发器 ---
  const handleInitialSend = (imageBlob: Blob | File) => {
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
      if (!specificQuestion) { 
        setError('请输入你要指定的题目信息。'); 
        return; 
      }
      const basePrompt = mode === 'solve' 
        ? '请只解答以下指定的题目，写出详细步骤：' 
        : '请只批改以下指定的题目，指出答案中的对错，如果答案错误就给出正确解法，回答正确就不用多说：';
      promptText = `${basePrompt}${specificQuestion}`;
    }
    
    // V24.0: 启动整页多题处理流程
    startMultiQuestionProcessing(imageBlob, promptText);
  };
  
  const onSelectFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      
      // 清除旧的错误信息
      setError('');
      
      // V23.0: 调用质量检测
      checkImageQuality(file);
      
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
        handleInitialSend(blob);
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
                <button onClick={() => handleInitialSend(fileRef.current!)} className="modern-button">
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
            {/* V24.0 新增：题目选择器（多题模式） */}
            {sessions.length > 1 && (
              <QuestionSelector
                count={sessions.length}
                activeIndex={activeSessionIndex}
                onSelect={setActiveSessionIndex}
                loadingStates={sessions.map(s => s.isLoading)}
                errorStates={sessions.map(s => !!s.error)}
              />
            )}
            
            {/* V24.0 动态内容：根据当前激活的会话渲染 */}
            {sessions.length > 0 && sessions[activeSessionIndex] && (() => {
              const activeSession = sessions[activeSessionIndex];
              
              return (
                <>
                  {/* 显示当前激活题目的图片 */}
                  <div className="solved-image-container chat-image-display">
                    <h3>
                      {sessions.length > 1 
                        ? `第 ${activeSessionIndex + 1} 题 / 共 ${sessions.length} 题` 
                        : "题目原文"}
                    </h3>
                    <img 
                      src={activeSession.imageSrc} 
                      alt={`题目 ${activeSessionIndex + 1}`} 
                      className="solved-image" 
                    />
                  </div>
                  
                  {/* 显示错误信息（如果有） */}
                  {activeSession.error && (
                    <div className="error" style={{ marginBottom: '1rem' }}>
                      {activeSession.error}
                    </div>
                  )}
                  
                  {/* 显示当前激活会话的聊天记录 */}
                  <div className="chat-messages">
                    {activeSession.messages.map((msg, index) => (
                      <div key={index} className={`message-bubble-wrapper ${msg.role}`}>
                        {msg.role === 'user' && <div className="avatar user-avatar">You</div>}
                        <div className={`message-bubble ${msg.role}`}>
                          <div className="message-content" dangerouslySetInnerHTML={{ __html: marked.parse(msg.content) }}></div>
                        </div>
                        {msg.role === 'assistant' && <div className="avatar assistant-avatar">AI</div>}
                      </div>
                    ))}
                    
                    {/* 加载状态指示器 */}
                    {activeSession.isLoading && (
                      <div className="message-bubble-wrapper assistant">
                        <div className="message-bubble assistant">
                          {activeSession.statusText ? (
                            <div className="status-text-inline">{activeSession.statusText}</div>
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
                  
                  {/* 交互区域：快捷按钮 + 输入框 */}
                  {activeSession.messages.length > 0 && !activeSession.isLoading && (
                    <>
                      {/* 快捷按钮 */}
                      {activeSession.showQuickButtons && (
                        <div className="quick-buttons-container">
                          <button 
                            className="quick-button quick-button-continue"
                            onClick={() => sendMessage("请继续回答", activeSessionIndex)}
                          >
                            <span className="quick-button-icon">▶️</span>
                            <span>请继续回答</span>
                          </button>
                          <button 
                            className="quick-button quick-button-check"
                            onClick={() => sendMessage("请检查刚才的回复是否有错误", activeSessionIndex)}
                          >
                            <span className="quick-button-icon">🔍</span>
                            <span>请检查是否有错误</span>
                          </button>
                        </div>
                      )}
                      
                      {/* 输入框 */}
                      <div className="chat-input-area">
                        <textarea
                          value={userInput}
                          onChange={(e) => setUserInput(e.target.value)}
                          placeholder="针对以上内容继续提问..."
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              if(userInput.trim()) sendMessage(userInput, activeSessionIndex);
                            }
                          }}
                        />
                        <button 
                          onClick={() => {if(userInput.trim()) sendMessage(userInput, activeSessionIndex)}} 
                          disabled={!userInput.trim()}
                        >
                          发送
                        </button>
                      </div>
                    </>
                  )}
                </>
              );
            })()}
            
            {/* V24.0 新增：全局处理中的覆盖层 */}
            {isProcessingSheet && (
              <div className="loading-overlay">
                <div className="loading-overlay-content">
                  <div className="loading-spinner"></div>
                  <p className="loading-text">{statusText}</p>
                </div>
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