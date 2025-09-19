// ==============================================================================
// 完整 App.tsx - 【V13.0 终极原生渲染版】
// ==============================================================================

import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { marked } from 'marked'; // 导入Marked.js用于类型安全
import './App.css';

import ReactCrop, { type Crop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';

// 声明全局MathJax对象，避免TypeScript报错
// 我们现在依赖于index.html中通过CDN加载的全局MathJax对象
declare global {
  interface Window {
    MathJax: {
      typesetPromise: (elements?: HTMLElement[]) => Promise<void>;
      // 可以根据需要添加更多MathJax的类型定义
    };
  }
}

// 主应用组件
function App() {
  // --- 状态定义 ---
  const [solution, setSolution] = useState<string>(''); // 现在存储的是原始Markdown
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  
  const [imgSrc, setImgSrc] = useState<string>('');
  const [crop, setCrop] = useState<Crop>();
  const [solvedImageSrc, setSolvedImageSrc] = useState<string>('');
  
  const [progress, setProgress] = useState<number>(0);
  const [statusText, setStatusText] = useState<string>('');
  
  // Refs
  const imgRef = useRef<HTMLImageElement | null>(null);
  const fileRef = useRef<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // 后端API地址
  const backendUrl = 'http://127.0.0.1:8000';
// ==============================================================================
// 完整 App.tsx - 第二部分: 核心逻辑函数
// ==============================================================================

  const onSelectFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSolution('');
      setError('');
      setSolvedImageSrc('');
      setProgress(0);
      setStatusText('');
      setCrop(undefined);
      fileRef.current = e.target.files[0];
      const reader = new FileReader();
      reader.addEventListener('load', () => setImgSrc(reader.result?.toString() || ''));
      reader.readAsDataURL(fileRef.current);
    }
  };

  const sendRequest = async (imageBlob: Blob | File, imageSrcForDisplay: string) => {
    setIsLoading(true);
    setSolution(''); // 清空旧答案的Markdown
    setError('');
    setSolvedImageSrc(imageSrcForDisplay);
    
    let progressInterval: number | null = null;
    try {
      setProgress(10);
      setStatusText('正在上传并识别图片...');
      
      const formData = new FormData();
      formData.append('file', imageBlob, 'image-to-solve.png');

      await new Promise(resolve => setTimeout(resolve, 1500)); 
      setProgress(40);
      setStatusText('AI导师正在进行深度推理与解答...');

      progressInterval = window.setInterval(() => {
          setProgress(p => (p < 90 ? p + 2 : p));
      }, 200);

      // 注意：我们期望后端返回纯文本/Markdown
      const response = await axios.post<string>(`${backendUrl}/solve`, formData);
      
      if(progressInterval) clearInterval(progressInterval);
      setProgress(100);
      setStatusText('解答生成完毕！');
      
      // 核心修改：直接存储原始Markdown，渲染工作交给useEffect
      setSolution(response.data);

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
        if (fileInputRef.current) fileInputRef.current.value = "";
      }, 1500);
    }
  }

  // --- 新增：使用useEffect来处理原生渲染 ---
  useEffect(() => {
    // 只有当solution有内容，且不在加载中时，才执行渲染
    if (solution && !isLoading) {
      const answerDiv = document.getElementById('answer-content');
      if (answerDiv) {
        // 步骤1: 用marked.js解析Markdown为HTML，并注入到div中
        // WARNING: 直接使用innerHTML有XSS风险，但在我们信任后端输出的情况下是可接受的
        answerDiv.innerHTML = marked.parse(solution);
        
        // 步骤2: 手动调用全局的MathJax对象，通知它去渲染这个新内容
        if (window.MathJax?.typesetPromise) {
          console.log("正在调用 MathJax.typesetPromise...");
          window.MathJax.typesetPromise([answerDiv]).catch((err) => console.error('MathJax typeset error:', err));
        }
      }
    }
  }, [solution, isLoading]); // 这个effect依赖于solution和isLoading的变化

  const handleSolveCroppedImage = () => {
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
      if (blob) sendRequest(blob, canvas.toDataURL('image/png'));
      else setError('无法生成裁剪后的图片。');
    }, 'image/png');
  };

  const handleSolveOriginalImage = () => {
    if (fileRef.current && imgSrc) {
      sendRequest(fileRef.current, imgSrc);
    } else {
      setError('找不到原始图片文件，请重新上传。');
    }
  }
  
  const handleCancelCrop = () => {
    setImgSrc('');
    setError('');
    setSolution('');
    setSolvedImageSrc('');
    setProgress(0);
    setStatusText('');
    fileRef.current = null;
  }
// ==============================================================================
// 完整 App.tsx - 第三部分: UI渲染 (JSX)
// ==============================================================================

  return (
    <div className="App">
      <header className="App-header">
        <h1>AI 拍照解题</h1>
        <p>上传题目图片，裁剪或直接解答！</p>
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

        {/* 解答显示区域 */}
        {solution && (
          <div className="solution-container card-container">
            {solvedImageSrc && (
              <div className="solved-image-container">
                <h3>题目原文</h3>
                <img src={solvedImageSrc} alt="已解答的题目" className="solved-image" />
              </div>
            )}
            <h2>解题详情：</h2>
            {/* --- 核心渲染修改在这里 --- */}
            {/* 我们只提供一个空的div容器，让useEffect去填充和渲染它 */}
            <div id="answer-content"></div>
          </div>
        )}

        {!isLoading && !solution && (
          <div className="card-container">
            {!imgSrc ? (
              <div className="upload-container" onClick={() => fileInputRef.current?.click()}>
                <input ref={fileInputRef} id="file-input" type="file" accept="image/*" onChange={onSelectFile} style={{ display: 'none' }} />
                <div className="upload-text">点击或拖拽图片到此区域</div>
                <div className="upload-button">选择文件</div>
              </div>
            ) : (
              <div className="crop-container">
                <ReactCrop crop={crop} onChange={c => setCrop(c)}>
                  <img ref={imgRef} src={imgSrc} alt="Crop preview" />
                </ReactCrop>
                <div className="crop-actions">
                  <button onClick={handleSolveOriginalImage} className="solve-direct-btn">直接解答</button>
                  <button onClick={handleSolveCroppedImage} disabled={!crop?.width || !crop?.height} className="solve-crop-btn">解答裁剪区域</button>
                  <button onClick={handleCancelCrop} className="cancel-btn">重新上传</button>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;