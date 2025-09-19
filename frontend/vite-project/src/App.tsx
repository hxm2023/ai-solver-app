// ==============================================================================
// 完整 App.tsx - 【V14.0 双模式架构版】
// ==============================================================================

import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { marked } from 'marked';
import './App.css';
import './ModeSelector.css'; // 引入新组件的样式

import ReactCrop, { type Crop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';

// 声明全局MathJax对象
declare global {
  interface Window {
    MathJax: any;
  }
}
// ==============================================================================
// 完整 App.tsx - 第二部分: 子组件定义
// ==============================================================================

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
              <span className="button-description">上传题目和你的答案，获取专业点评</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

// ==============================================================================
// 完整 App.tsx - 第三部分: MainApp组件 (V14.1 终极完整版)
// ==============================================================================

interface MainAppProps {
  mode: 'solve' | 'review';
  onBack: () => void;
}

function MainApp({ mode, onBack }: MainAppProps) {
  // --- 所有状态和Refs定义 ---
  const [solution, setSolution] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  
  const [questionImgSrc, setQuestionImgSrc] = useState<string>('');
  const [answerImgSrc, setAnswerImgSrc] = useState<string>('');
  const [croppingFor, setCroppingFor] = useState<'question' | 'answer' | null>(null);
  
  const [crop, setCrop] = useState<Crop>();
  const [solvedQuestionImg, setSolvedQuestionImg] = useState<string>('');
  const [solvedAnswerImg, setSolvedAnswerImg] = useState<string>('');
  
  const [progress, setProgress] = useState<number>(0);
  const [statusText, setStatusText] = useState<string>('');

  const imgRef = useRef<HTMLImageElement | null>(null);
  const questionFileRef = useRef<File | null>(null);
  const answerFileRef = useRef<File | null>(null);
  const questionInputRef = useRef<HTMLInputElement | null>(null);
  const answerInputRef = useRef<HTMLInputElement | null>(null);

  const backendUrl = 'http://127.0.0.1:8000';

  // --- 核心逻辑函数 ---

  const onSelectFile = (e: React.ChangeEvent<HTMLInputElement>, type: 'question' | 'answer') => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      const reader = new FileReader();
      reader.addEventListener('load', () => {
        const resultSrc = reader.result?.toString() || '';
        if (type === 'question') {
          setQuestionImgSrc(resultSrc);
          questionFileRef.current = file;
        } else {
          setAnswerImgSrc(resultSrc);
          answerFileRef.current = file;
        }
        // 【修复3】: 上传后不清空裁剪界面，而是让用户自己决定
        // setCroppingFor(type);
      });
      reader.readAsDataURL(file);
    }
  };

  const sendRequest = async (apiUrl: string, formData: FormData, qImg: string, aImg?: string) => {
    setIsLoading(true);
    setSolution('');
    setError('');
    setSolvedQuestionImg(qImg);
    if (aImg) setSolvedAnswerImg(aImg);
    
    let progressInterval: number | null = null;
    try {
      setProgress(10);
      setStatusText('正在上传并识别图片...');
      
      await new Promise(resolve => setTimeout(resolve, 1500));
      setProgress(40);
      setStatusText(mode === 'solve' ? 'AI导师正在深度推理中...' : 'AI批改官正在仔细审阅中...');

      progressInterval = window.setInterval(() => {
          setProgress(p => (p < 90 ? p + 2 : p));
      }, 200);

      // 后端可能返回JSON {solution: "..."} 或纯文本
      // 我们用 any 类型来接收，然后在下面进行检查
      const response = await axios.post<any>(apiUrl, formData);
      
      if(progressInterval) clearInterval(progressInterval);
      setProgress(100);
      setStatusText('处理完成！');

      // --- 【核心修复】: 对后端返回的数据进行类型检查 ---
      let markdownContent = '';
      if (typeof response.data === 'string') {
        // 如果后端直接返回了字符串
        markdownContent = response.data;
      } else if (response.data && typeof response.data.solution === 'string') {
        // 如果后端返回了 { solution: "..." } 这样的JSON对象
        markdownContent = response.data.solution;
      } else {
        // 其他未知情况，抛出错误
        throw new Error("从后端接收到的数据格式不正确。");
      }
      
      setSolution(markdownContent); // 保证设置到state里的一定是字符串

    } catch (err) {
      if(progressInterval) clearInterval(progressInterval);
      let errorMessage = '糟糕，出错了！可能是图片无法识别或服务器繁忙。';
      if (axios.isAxiosError(err) && err.response) {
        errorMessage += ` 错误详情: ${err.response.data.detail || err.message}`;
      } else if (err instanceof Error) {
        errorMessage += ` 错误详情: ${err.message}`;
      }
      setError(errorMessage);
      console.error("请求错误:", err);
      setProgress(0);
    } finally {
      setTimeout(() => {
        setIsLoading(false);
        if (questionInputRef.current) questionInputRef.current.value = "";
        if (answerInputRef.current) answerInputRef.current.value = "";
      }, 1500);
    }
  };

  // --- 【核心修复】: 渲染触发逻辑 ---
  useEffect(() => {
    // 只有当solution有内容时，才执行渲染
    if (solution) {
      const answerDiv = document.getElementById('answer-content');
      if (answerDiv) {
        // 先解析，再渲染
        answerDiv.innerHTML = marked.parse(solution);
        if (window.MathJax?.typesetPromise) {
          window.MathJax.typesetPromise([answerDiv]).catch((err) => console.error('MathJax typeset error:', err));
        }
      }
    } else {
      // 如果solution为空，确保清空DOM
      const answerDiv = document.getElementById('answer-content');
      if (answerDiv) {
        answerDiv.innerHTML = '';
      }
    }
  }, [solution]); // <<< 关键：只依赖于solution的变化！


  const handleConfirmCrop = () => {
    if (!crop || !imgRef.current || !croppingFor) return;

    const canvas = document.createElement('canvas');
    const scaleX = imgRef.current.naturalWidth / imgRef.current.width;
    const scaleY = imgRef.current.naturalHeight / imgRef.current.height;
    canvas.width = Math.floor(crop.width * scaleX);
    canvas.height = Math.floor(crop.height * scaleY);
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      setError('无法处理图片，浏览器支持不足.');
      return;
    }
    ctx.drawImage(
      imgRef.current,
      crop.x * scaleX,
      crop.y * scaleY,
      crop.width * scaleX,
      crop.height * scaleY,
      0,
      0,
      canvas.width,
      canvas.height
    );
    canvas.toBlob((blob) => {
      if (blob) {
        const croppedSrc = canvas.toDataURL('image/png');
        const fileName = croppingFor === 'question' ? 'question.png' : 'answer.png';
        const file = new File([blob], fileName, { type: "image/png" });

        if (croppingFor === 'question') {
          questionFileRef.current = file;
          setQuestionImgSrc(croppedSrc);
        } else {
          answerFileRef.current = file;
          setAnswerImgSrc(croppedSrc);
        }
      }
      setCroppingFor(null);
    }, 'image/png');
  };

  const handleStartProcess = () => {
    const formData = new FormData();
    let apiUrl = '';
    
    if (mode === 'solve') {
      if (!questionFileRef.current) {
        setError("请先上传题目图片。");
        return;
      }
      apiUrl = `${backendUrl}/solve`;
      formData.append('file', questionFileRef.current);
      sendRequest(apiUrl, formData, questionImgSrc);

    } else if (mode === 'review') {
      if (!questionFileRef.current || !answerFileRef.current) {
        setError("请确保已上传【题目】和【你的答案】两张图片。");
        return;
      }
      apiUrl = `${backendUrl}/review`;
      formData.append('question_image', questionFileRef.current);
      formData.append('answer_image', answerFileRef.current);
      sendRequest(apiUrl, formData, questionImgSrc, answerImgSrc);
    }
  };

  // ==============================================================================
// 完整 App.tsx - MainApp UI渲染 (V15.1 可选裁剪UI版)
// ==============================================================================

  // --- MainApp 组件的 UI 渲染 ---

  // 如果正在裁剪，显示专门的裁剪界面
  if (croppingFor) {
    const imgSrc = croppingFor === 'question' ? questionImgSrc : answerImgSrc;
    return (
      <div className="App">
        <header className="App-header">
          <h1>正在裁剪: {croppingFor === 'question' ? '题目图片' : '答案图片'}</h1>
          <button onClick={() => setCroppingFor(null)} className="back-button">返回</button>
        </header>
        <main className="App-main">
          <div className="card-container">
            <div className="crop-container">
              <p className='crop-instruction'>请拖动选框以选择你需要的区域</p>
              <ReactCrop crop={crop} onChange={c => setCrop(c)}>
                <img ref={imgRef} src={imgSrc} alt="Crop preview" />
              </ReactCrop>
              <div className="crop-actions">
                <button onClick={handleConfirmCrop} className="solve-crop-btn">确认裁剪</button>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }
  
  // 主上传和显示界面
  return (
    <div className="App">
      <header className="App-header">
        <h1>{mode === 'solve' ? 'AI 智能解题' : 'AI 批改作业'}</h1>
        <p>{mode === 'solve' ? '上传题目，获取详细解答' : '上传题目和你的答案，获取专业点评'}</p>
        <button onClick={onBack} className="back-button">返回模式选择</button>
      </header>
      <main className="App-main">
        {/* 加载和错误显示区域 */}
        {isLoading && (
          <div className="status-container card-container">
            <div className="status-text">{statusText}</div>
            <div className="progress-bar">
              <div className="progress-bar-inner" style={{ width: `${progress}%` }}></div>
            </div>
          </div>
        )}
        {error && <div className="error">{error}</div>}
        
        {/* 解答显示区域 */}
        {solution && (
          <div className="solution-container card-container">
            <div className="solved-image-container">
              <h3>题目原文</h3>
              <img src={solvedQuestionImg} alt="已解答的题目" className="solved-image" />
              {mode === 'review' && solvedAnswerImg && (
                <>
                  <h3 style={{marginTop: '1rem'}}>你的答案</h3>
                  <img src={solvedAnswerImg} alt="你的答案" className="solved-image" />
                </>
              )}
            </div>
            <h2>{mode === 'solve' ? '解题详情' : '批改报告'}:</h2>
            <div id="answer-content"></div>
          </div>
        )}
        
        {/* 主上传界面 (仅在非加载且无答案时显示) */}
        {!isLoading && !solution && (
          <div className="card-container">
            <div className="upload-grid"> {/* 使用Grid布局 */}
              {/* --- 题目上传区 --- */}
              <div className="upload-section">
                <h3>{questionImgSrc ? "题目图片" : "第一步：上传题目"}</h3>
                {!questionImgSrc ? (
                   <div className="upload-box" onClick={() => questionInputRef.current?.click()}>
                      <input ref={questionInputRef} id="q-input" type="file" accept="image/*" onChange={(e) => onSelectFile(e, 'question')} style={{ display: 'none' }} />
                      <span>+</span>
                      <p>选择文件</p>
                   </div>
                ) : (
                  <div className="thumbnail-container">
                    <img src={questionImgSrc} className="thumbnail" alt="题目缩略图" />
                    <button onClick={() => setCroppingFor('question')} className="crop-button">裁剪</button>
                  </div>
                )}
              </div>

              {/* --- 答案上传区 (仅在批改模式下显示) --- */}
              {mode === 'review' && (
                <div className="upload-section">
                  <h3>{answerImgSrc ? "你的答案图片" : "第二步：上传答案"}</h3>
                  {!answerImgSrc ? (
                    <div className="upload-box" onClick={() => answerInputRef.current?.click()}>
                       <input ref={answerInputRef} id="a-input" type="file" accept="image/*" onChange={(e) => onSelectFile(e, 'answer')} style={{ display: 'none' }} />
                       <span>+</span>
                       <p>选择文件</p>
                    </div>
                  ) : (
                    <div className="thumbnail-container">
                      <img src={answerImgSrc} className="thumbnail" alt="答案缩略图" />
                      <button onClick={() => setCroppingFor('answer')} className="crop-button">裁剪</button>
                    </div>
                  )}
                </div>
              )}
            </div>
            
            {/* --- 总提交按钮 --- */}
            <div className="main-action-button-container">
              <button 
                onClick={handleStartProcess} 
                className="solve-direct-btn"
                // 按钮禁用逻辑
                disabled={
                  mode === 'solve' ? !questionFileRef.current : (!questionFileRef.current || !answerFileRef.current)
                }
              >
                {mode === 'solve' ? '开始智能解题' : '开始智能批改'}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
// --- 顶层App组件 (只负责模式切换) ---
function App() {
  const [mode, setMode] = useState<'solve' | 'review' | null>(null);

  if (!mode) {
    return <ModeSelector onSelectMode={setMode} />;
  }

  return <MainApp mode={mode} onBack={() => setMode(null)} />;
}

export default App;