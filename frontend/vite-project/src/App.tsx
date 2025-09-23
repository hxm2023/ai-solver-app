// ==============================================================================
// 完整 App.tsx - 【V18.0 终极单图统一版】
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
  interface Window {
    MathJax: any;
  }
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


// --- 主应用界面组件 ---
interface MainAppProps {
  mode: 'solve' | 'review';
  onBack: () => void;
}
function MainApp({ mode, onBack }: MainAppProps) {
  const [solution, setSolution] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [imageSrc, setImageSrc] = useState<string>('');
  const [crop, setCrop] = useState<Crop>();
  const [solvedImage, setSolvedImage] = useState<string>('');
  const [progress, setProgress] = useState<number>(0);
  const [statusText, setStatusText] = useState<string>('');
  
  const [solveType, setSolveType] = useState<'single' | 'full' | 'specific'>('single');
  const [specificQuestion, setSpecificQuestion] = useState<string>('');
  
  const imgRef = useRef<HTMLImageElement | null>(null);
  const fileRef = useRef<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const backendUrl = 'http://127.0.0.1:8000';
// ==============================================================================
// 完整 App.tsx - 第二部分: 核心逻辑函数
// ==============================================================================

  const onSelectFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSolution('');
      setError('');
      setSolvedImage('');
      setProgress(0);
      setStatusText('');
      setCrop(undefined);
      const file = e.target.files[0];
      fileRef.current = file;
      const reader = new FileReader();
      reader.addEventListener('load', () => setImageSrc(reader.result?.toString() || ''));
      reader.readAsDataURL(file);
    }
  };

  const sendRequest = async (imageBlob: Blob | File, imageSrcForDisplay: string, promptText: string) => {
    setIsLoading(true);
    setSolution('');
    setError('');
    setSolvedImage(imageSrcForDisplay);
    
    let progressInterval: number | null = null;
    try {
      setProgress(10);
      setStatusText('正在上传图片...');
      
      const formData = new FormData();
      const apiUrl = mode === 'solve' ? `${backendUrl}/solve` : `${backendUrl}/review`;
      
      formData.append('file', imageBlob);
      formData.append('prompt_text', promptText);

      await new Promise(resolve => setTimeout(resolve, 500));
      setProgress(20);
      setStatusText('图片已送达AI，正在进行深度分析...');

      progressInterval = window.setInterval(() => {
          setProgress(p => (p < 95 ? p + 1 : p));
      }, 400);

      const response = await axios.post<string>(apiUrl, formData);
      
      if(progressInterval) clearInterval(progressInterval);
      setProgress(100);
      setStatusText('处理完成！');
      
      setSolution(response.data);

    } catch (err) {
      if(progressInterval) clearInterval(progressInterval);
      let errorMessage = '糟糕，出错了！可能是图片无法识别或服务器繁忙。';
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        errorMessage = `错误: ${err.response.data.detail}`;
      } else if (err instanceof Error) {
        errorMessage = `错误: ${err.message}`;
      }
      setError(errorMessage);
      console.error("请求错误:", err);
      setProgress(0);
    } finally {
      setTimeout(() => setIsLoading(false), 1500);
    }
  };

  useEffect(() => {
    if (solution && !isLoading) {
      const answerDiv = document.getElementById('answer-content');
      if (answerDiv) {
        answerDiv.innerHTML = marked.parse(solution);
        if (window.MathJax?.typesetPromise) {
          window.MathJax.typesetPromise([answerDiv]).catch((err) => console.error('MathJax typeset error:', err));
        }
      }
    }
  }, [solution, isLoading]);

  const handleProcessImage = (useOriginal: boolean) => {
    let imageFile: Blob | File | null = useOriginal ? fileRef.current : null;
    let imageSrcForDisplay = imageSrc;

    // 动态生成Prompt
    let promptText = '';
    const solveBase = '请详细解答';
    const reviewBase = '请详细批改这张同时包含题目和答案的图片。';
    
    if (solveType === 'single') {
      promptText = mode === 'solve' ? `${solveBase}这道题目。` : `${reviewBase}`;
    } else if (solveType === 'full') {
      promptText = mode === 'solve' ? `${solveBase}这张图片中的所有题目。` : `${reviewBase}`;
    } else { // specific
      if (!specificQuestion) { setError('请输入你要指定的题目信息。'); return; }
      const basePrompt = mode === 'solve' ? `${solveBase}这道题目：` : `${reviewBase}，特别是关于：`;
      promptText = `${basePrompt} ${specificQuestion}`;
    }

    if (!useOriginal) {
        if (!crop || !imgRef.current || !crop.width || !crop.height) { setError('请先在图片上拖动以选择一个裁剪区域。'); return; }
        const canvas = document.createElement('canvas');
        const scaleX = imgRef.current.naturalWidth / imgRef.current.width;
        const scaleY = imgRef.current.naturalHeight / imgRef.current.height;
        canvas.width = Math.floor(crop.width * scaleX);
        canvas.height = Math.floor(crop.height * scaleY);
        const ctx = canvas.getContext('2d');
        if (!ctx) { setError('无法处理图片，浏览器支持不足。'); return; }
        ctx.drawImage(imgRef.current, crop.x * scaleX, crop.y * scaleY, crop.width * scaleX, crop.height * scaleY, 0, 0, canvas.width, canvas.height);
        
        imageSrcForDisplay = canvas.toDataURL('image/png');
        canvas.toBlob((blob) => {
            if (blob) sendRequest(blob, imageSrcForDisplay, promptText);
            else setError('无法生成裁剪后的图片。');
        }, 'image/png');
    } else if (imageFile) {
        sendRequest(imageFile, imageSrcForDisplay, promptText);
    } else {
        setError('找不到原始图片文件，请重新上传。');
    }
  };
// ==============================================================================
// 完整 App.tsx - 第三部分: UI渲染 (JSX)
// ==============================================================================

  return (
    <div className="App">
      <header className="App-header">
        <h1>{mode === 'solve' ? 'AI 智能解题' : 'AI 批改作业'}</h1>
        <p>
          {mode === 'solve' 
            ? '上传题目，获取详细解答' 
            : '上传包含题目与答案的图片，获取专业点评'
          }
        </p>
        <button onClick={onBack} className="back-button">返回模式选择</button>
      </header>
      <main className="App-main">
        {isLoading && (
          <div className="status-container card-container">
            <div className="status-text">{statusText}</div>
            <div className="progress-bar">
              <div className="progress-bar-inner" style={{ width: `${progress}%` }}></div>
            </div>
          </div>
        )}
        {error && <div className="error">{error}</div>}
        
        {solution && (
          <div className="solution-container card-container">
            {solvedImage && (
              <div className="solved-image-container">
                <h3>{mode === 'solve' ? '题目原文' : '你的图片'}</h3>
                <img src={solvedImage} alt="已解答的图片" className="solved-image" />
              </div>
            )}
            <h2>{mode === 'solve' ? '解题详情' : '批改报告'}:</h2>
            <div id="answer-content"></div>
          </div>
        )}
        
        {!isLoading && !solution && (
          <div className="card-container">
            <div className="solve-type-selector">
              <button className={solveType === 'single' ? 'active' : ''} onClick={() => setSolveType('single')}>
                {mode === 'solve' ? '解单个题目' : '批改单个题目'}
              </button>
              <button className={solveType === 'full' ? 'active' : ''} onClick={() => setSolveType('full')}>
                {mode === 'solve' ? '解整张图片' : '批改整张图片'}
              </button>
              <button className={solveType === 'specific' ? 'active' : ''} onClick={() => setSolveType('specific')}>
                指定题目
              </button>
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
                    <span>+</span>
                    <p>选择文件</p>
                 </div>
              ) : (
                <div className="crop-container">
                  <p className='crop-instruction'>（可选）请拖动选框以选择特定区域进行分析</p>
                  <ReactCrop crop={crop} onChange={c => setCrop(c)}>
                    <img ref={imgRef} src={imageSrc} alt="Crop preview" />
                  </ReactCrop>
                </div>
              )}
            </div>
            
            {imageSrc && (
              <div className="main-action-button-container">
                <button 
                  onClick={() => handleProcessImage(true)}
                  className="modern-button"
                  disabled={isLoading}
                >
                  {mode === 'solve' ? '解析整张图片' : '批改整张图片'}
                </button>
                <button 
                  onClick={() => handleProcessImage(false)}
                  className="modern-button"
                  disabled={isLoading || !crop?.width || !crop?.height}
                  style={{backgroundImage: 'linear-gradient(90deg, #6c757d 0%, #343a40 100%)'}}
                >
                  仅处理裁剪区域
                </button>
              </div>
            )}
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
















































// // ==============================================================================
// // 完整 App.tsx - 【V15.2 终极完整版，包含所有组件】
// // ==============================================================================

// import React, { useState, useRef, useEffect } from 'react';
// import axios from 'axios';
// import { marked } from 'marked';
// import './App.css';
// import './ModeSelector.css';

// import ReactCrop, { type Crop } from 'react-image-crop';
// import 'react-image-crop/dist/ReactCrop.css';

// // 声明全局MathJax对象
// declare global {
//   interface Window {
//     MathJax: any;
//   }
// }
// // ==============================================================================
// // 完整 App.tsx - 第二部分: 子组件定义
// // ==============================================================================

// // --- 【新增】模式选择器组件 ---
// interface ModeSelectorProps {
//   onSelectMode: (mode: 'solve' | 'review') => void;
// }
// const ModeSelector: React.FC<ModeSelectorProps> = ({ onSelectMode }) => {
//   return (
//     <div className="mode-selector-container">
//       <div className="mode-selector-card">
//         <h1 className="mode-selector-title">请选择功能模式</h1>
//         <p className="mode-selector-subtitle">你想让AI为你解答难题，还是批改你的作业？</p>
//         <div className="mode-buttons">
//           <button className="mode-button" onClick={() => onSelectMode('solve')}>
//             <span className="button-icon">🧠</span>
//             <div>
//               <span className="button-text">AI 智能解题</span>
//               <span className="button-description">上传题目，获取详细解答</span>
//             </div>
//           </button>
//           <button className="mode-button" onClick={() => onSelectMode('review')}>
//             <span className="button-icon">📝</span>
//             <div>
//               <span className="button-text">AI 批改作业</span>
//               <span className="button-description">上传题目和你的答案，获取专业点评</span>
//             </div>
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// };

// // --- 主应用界面组件 ---
// interface MainAppProps {
//   mode: 'solve' | 'review';
//   onBack: () => void;
// }
// function MainApp({ mode, onBack }: MainAppProps) {
//   // --- 所有状态和Refs定义 ---
//   const [solution, setSolution] = useState<string>('');
//   const [isLoading, setIsLoading] = useState<boolean>(false);
//   const [error, setError] = useState<string>('');
//   const [questionImgSrc, setQuestionImgSrc] = useState<string>('');
//   const [answerImgSrc, setAnswerImgSrc] = useState<string>('');
//   const [croppingFor, setCroppingFor] = useState<'question' | 'answer' | null>(null);
//   const [crop, setCrop] = useState<Crop>();
//   const [solvedQuestionImg, setSolvedQuestionImg] = useState<string>('');
//   const [solvedAnswerImg, setSolvedAnswerImg] = useState<string>('');
//   const [progress, setProgress] = useState<number>(0);
//   const [statusText, setStatusText] = useState<string>('');
//   const imgRef = useRef<HTMLImageElement | null>(null);
//   const questionFileRef = useRef<File | null>(null);
//   const answerFileRef = useRef<File | null>(null);
//   const questionInputRef = useRef<HTMLInputElement | null>(null);
//   const answerInputRef = useRef<HTMLInputElement | null>(null);
//   const backendUrl = 'http://127.0.0.1:8000';

//   // --- 核心逻辑函数 ---
//   const onSelectFile = (e: React.ChangeEvent<HTMLInputElement>, type: 'question' | 'answer') => {
//     if (e.target.files && e.target.files.length > 0) {
//       const file = e.target.files[0];
//       const reader = new FileReader();
//       reader.addEventListener('load', () => {
//         const resultSrc = reader.result?.toString() || '';
//         if (type === 'question') {
//           setQuestionImgSrc(resultSrc);
//           questionFileRef.current = file;
//         } else {
//           setAnswerImgSrc(resultSrc);
//           answerFileRef.current = file;
//         }
//       });
//       reader.readAsDataURL(file);
//     }
//   };

//   const sendRequest = async (apiUrl: string, formData: FormData, qImg: string, aImg?: string) => {
//     setIsLoading(true);
//     setSolution('');
//     setError('');
//     setSolvedQuestionImg(qImg);
//     if (aImg) setSolvedAnswerImg(aImg);
    
//     let progressInterval: number | null = null;
//     try {
//       setProgress(10);
//       setStatusText('正在上传并识别图片...');
      
//       await new Promise(resolve => setTimeout(resolve, 1500));
//       setProgress(40);
//       setStatusText(mode === 'solve' ? 'AI导师正在深度推理中...' : 'AI批改官正在仔细审阅中...');

//       progressInterval = window.setInterval(() => {
//           setProgress(p => (p < 90 ? p + 2 : p));
//       }, 200);

//       const response = await axios.post<any>(apiUrl, formData);
      
//       if(progressInterval) clearInterval(progressInterval);
//       setProgress(100);
//       setStatusText('处理完成！');

//       let markdownContent = '';
//       if (typeof response.data === 'string') {
//         markdownContent = response.data;
//       } else if (response.data && typeof response.data.solution === 'string') {
//         markdownContent = response.data.solution;
//       } else {
//         throw new Error("从后端接收到的数据格式不正确。");
//       }
      
//       setSolution(markdownContent);

//     } catch (err) {
//       if(progressInterval) clearInterval(progressInterval);
//       let errorMessage = '糟糕，出错了！可能是图片无法识别或服务器繁忙。';
//       if (axios.isAxiosError(err) && err.response) {
//         errorMessage += ` 错误详情: ${err.response.data.detail || err.message}`;
//       } else if (err instanceof Error) {
//         errorMessage += ` 错误详情: ${err.message}`;
//       }
//       setError(errorMessage);
//       console.error("请求错误:", err);
//       setProgress(0);
//     } finally {
//       setTimeout(() => {
//         setIsLoading(false);
//         if (questionInputRef.current) questionInputRef.current.value = "";
//         if (answerInputRef.current) answerInputRef.current.value = "";
//       }, 1500);
//     }
//   };

//   useEffect(() => {
//     if (solution && !isLoading) {
//       const answerDiv = document.getElementById('answer-content');
//       if (answerDiv) {
//         answerDiv.innerHTML = marked.parse(solution);
//         if (window.MathJax?.typesetPromise) {
//           window.MathJax.typesetPromise([answerDiv]).catch((err) => console.error('MathJax typeset error:', err));
//         }
//       }
//     } else if (!solution) {
//       const answerDiv = document.getElementById('answer-content');
//       if (answerDiv) {
//         answerDiv.innerHTML = '';
//       }
//     }
//   }, [solution, isLoading]);

//   const handleConfirmCrop = () => {
//     if (!crop || !imgRef.current || !croppingFor) return;
//     const canvas = document.createElement('canvas');
//     const scaleX = imgRef.current.naturalWidth / imgRef.current.width;
//     const scaleY = imgRef.current.naturalHeight / imgRef.current.height;
//     canvas.width = Math.floor(crop.width * scaleX);
//     canvas.height = Math.floor(crop.height * scaleY);
//     const ctx = canvas.getContext('2d');
//     if (!ctx) {
//       setError('无法处理图片，浏览器支持不足.');
//       return;
//     }
//     ctx.drawImage(imgRef.current, crop.x * scaleX, crop.y * scaleY, crop.width * scaleX, crop.height * scaleY, 0, 0, canvas.width, canvas.height);
//     canvas.toBlob((blob) => {
//       if (blob) {
//         const croppedSrc = canvas.toDataURL('image/png');
//         const fileName = croppingFor === 'question' ? 'question.png' : 'answer.png';
//         const file = new File([blob], fileName, { type: "image/png" });
//         if (croppingFor === 'question') {
//           questionFileRef.current = file;
//           setQuestionImgSrc(croppedSrc);
//         } else {
//           answerFileRef.current = file;
//           setAnswerImgSrc(croppedSrc);
//         }
//       }
//       setCroppingFor(null);
//     }, 'image/png');
//   };

//   const handleStartProcess = () => {
//     const formData = new FormData();
//     let apiUrl = '';
    
//     if (mode === 'solve') {
//       if (!questionFileRef.current) {
//         setError("请先上传题目图片。");
//         return;
//       }
//       apiUrl = `${backendUrl}/solve`;
//       formData.append('file', questionFileRef.current);
//       sendRequest(apiUrl, formData, questionImgSrc);
//     } else if (mode === 'review') {
//       if (!questionFileRef.current || !answerFileRef.current) {
//         setError("请确保已上传【题目】和【你的答案】两张图片。");
//         return;
//       }
//       apiUrl = `${backendUrl}/review`;
//       formData.append('question_image', questionFileRef.current);
//       formData.append('answer_image', answerFileRef.current);
//       sendRequest(apiUrl, formData, questionImgSrc, answerImgSrc);
//     }
//   };

//   // --- UI渲染 (JSX) ---
//   if (croppingFor) {
//     const imgSrc = croppingFor === 'question' ? questionImgSrc : answerImgSrc;
//     return (
//       <div className="App">
//         <header className="App-header">
//           <h1>正在裁剪: {croppingFor === 'question' ? '题目图片' : '答案图片'}</h1>
//           <button onClick={() => setCroppingFor(null)} className="back-button">返回</button>
//         </header>
//         <main className="App-main">
//           <div className="card-container">
//             <div className="crop-container">
//               <p className='crop-instruction'>请拖动选框以选择你需要的区域</p>
//               <ReactCrop crop={crop} onChange={c => setCrop(c)}>
//                 <img ref={imgRef} src={imgSrc} alt="Crop preview" />
//               </ReactCrop>
//               <div className="crop-actions">
//                 <button onClick={handleConfirmCrop} className="solve-crop-btn">确认裁剪</button>
//               </div>
//             </div>
//           </div>
//         </main>
//       </div>
//     );
//   }
  
//   return (
//     <div className="App">
//       <header className="App-header">
//         <h1>{mode === 'solve' ? 'AI 智能解题' : 'AI 批改作业'}</h1>
//         <p>{mode === 'solve' ? '上传题目，获取详细解答' : '上传题目和你的答案，获取专业点评'}</p>
//         <button onClick={onBack} className="back-button">返回模式选择</button>
//       </header>
//       <main className="App-main">
//         {isLoading && (
//           <div className="status-container card-container">
//             <div className="status-text">{statusText}</div>
//             <div className="progress-bar">
//               <div className="progress-bar-inner" style={{ width: `${progress}%` }}></div>
//             </div>
//           </div>
//         )}
//         {error && <div className="error">{error}</div>}
        
//         {solution && (
//           <div className="solution-container card-container">
//             <div className="solved-image-container">
//               <h3>题目原文</h3>
//               <img src={solvedQuestionImg} alt="已解答的题目" className="solved-image" />
//               {mode === 'review' && solvedAnswerImg && (
//                 <>
//                   <h3 style={{marginTop: '1rem'}}>你的答案</h3>
//                   <img src={solvedAnswerImg} alt="你的答案" className="solved-image" />
//                 </>
//               )}
//             </div>
//             <h2>{mode === 'solve' ? '解题详情' : '批改报告'}:</h2>
//             <div id="answer-content"></div>
//           </div>
//         )}
        
//         {!isLoading && !solution && (
//           <div className="card-container">
//             <div className="upload-grid">
//               <div className="upload-section">
//                 <h3>{questionImgSrc ? "已上传题目 (点击图片可重新裁剪)" : "第一步：上传题目图片"}</h3>
//                 {!questionImgSrc ? (
//                    <div className="upload-box" onClick={() => questionInputRef.current?.click()}>
//                       <input ref={questionInputRef} id="q-input" type="file" accept="image/*" onChange={(e) => onSelectFile(e, 'question')} style={{ display: 'none' }} />
//                       <span>+</span>
//                       <p>选择文件</p>
//                    </div>
//                 ) : (
//                   <div className="thumbnail-container">
//                     <img src={questionImgSrc} className="thumbnail" alt="题目缩略图" onClick={() => setCroppingFor('question')} />
//                     <button onClick={() => setCroppingFor('question')} className="crop-button">裁剪</button>
//                   </div>
//                 )}
//               </div>
//               {mode === 'review' && (
//                 <div className="upload-section">
//                   <h3>{answerImgSrc ? "已上传你的答案 (点击图片可重新裁剪)" : "第二步：上传你的答案图片"}</h3>
//                   {!answerImgSrc ? (
//                     <div className="upload-box" onClick={() => answerInputRef.current?.click()}>
//                        <input ref={answerInputRef} id="a-input" type="file" accept="image/*" onChange={(e) => onSelectFile(e, 'answer')} style={{ display: 'none' }} />
//                        <span>+</span>
//                        <p>选择文件</p>
//                     </div>
//                   ) : (
//                     <div className="thumbnail-container">
//                       <img src={answerImgSrc} className="thumbnail" alt="答案缩略图" onClick={() => setCroppingFor('answer')} />
//                       <button onClick={() => setCroppingFor('answer')} className="crop-button">裁剪</button>
//                     </div>
//                   )}
//                 </div>
//               )}
//             </div>
            
//             <div className="main-action-button-container">
//               <button 
//                 onClick={handleStartProcess} 
//                 className="solve-direct-btn"
//                 disabled={
//                   mode === 'solve' ? !questionFileRef.current : (!questionFileRef.current || !answerFileRef.current)
//                 }
//               >
//                 {mode === 'solve' ? '开始智能解题' : '开始智能批改'}
//               </button>
//             </div>
//           </div>
//         )}
//       </main>
//     </div>
//   );
// }
// // ==============================================================================
// // 完整 App.tsx - 第三部分: 顶层App组件
// // ==============================================================================

// function App() {
//   const [mode, setMode] = useState<'solve' | 'review' | null>(null);

//   if (!mode) {
//     return <ModeSelector onSelectMode={setMode} />;
//   }

//   return <MainApp mode={mode} onBack={() => setMode(null)} />;
// }

// export default App;