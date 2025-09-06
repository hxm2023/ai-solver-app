// // ==============================================================================
// // 完整 App.tsx - 【V8.1 激进格式化 + 终极美化版】
// // ==============================================================================

// import React, { useState, useRef } from 'react';
// import axios from 'axios';
// import ReactMarkdown from 'react-markdown';
// import remarkMath from 'remark-math';
// import rehypeKatex from 'rehype-katex';
// import 'katex/dist/katex.min.css';
// import './App.css';


// // 导入裁剪库的组件和类型
// import ReactCrop, { type Crop } from 'react-image-crop';
// import 'react-image-crop/dist/ReactCrop.css';


// // --- 【V8.3 终极转义版】的格式化函数 ---
// function finalFormatAIResponse(text: string): string {
//     // 预处理
//     let processedText = text.replace(/### 解题详情：|### 题目解答|### 解题步骤/gi, '').trim();

//     // 步骤1: 使用$$...$$作为分隔符，将文本分割成一个数组
//     const parts = processedText.split(/(\$\$(?:.|\n)*?\$\$)/g);

//     const formattedParts = parts.map((part, index) => {
//         // 步骤2: 分别治理
//         // 如果当前部分是块级公式，不做任何处理，原样返回
//         if (index % 2 === 1) {
//             return part;
//         }

//         // 如果当前部分是普通文本，我们在这里对它进行精细处理
//         let textPart = part;

//         // 规则A: 智能处理括号
//         textPart = textPart.replace(/(?<!\\)\(([\s\S]*?)(?<!\\)\)/g, (match, content) => {
//             const cleanContent = content.trim();
//             if (cleanContent.includes('$') || cleanContent === '') return match;
//             if (/[\u4e00-\u9fa5]/.test(cleanContent) || cleanContent.split(' ').length > 5) return match;
//             return `$${cleanContent}$`;
//         });
        
//         // 规则B: 处理 \[ ... \]
//         textPart = textPart.replace(/\\\[([\s\S]*?)\\\]/g, '$$$$$1$$$$');

//         return textPart;
//     });

//     // 步骤3: 重新拼接
//     return formattedParts.join('');
// }


// // 主应用组件
// function App() {
//   // --- 状态定义 ---
//   const [solution, setSolution] = useState<string>('');
//   const [isLoading, setIsLoading] = useState<boolean>(false);
//   const [error, setError] = useState<string>('');
  
//   const [imgSrc, setImgSrc] = useState<string>('');
//   const [crop, setCrop] = useState<Crop>();
//   const [solvedImageSrc, setSolvedImageSrc] = useState<string>('');
  
//   const [progress, setProgress] = useState<number>(0);
//   const [statusText, setStatusText] = useState<string>('');
  
//   // Refs
//   const imgRef = useRef<HTMLImageElement | null>(null);
//   const fileRef = useRef<File | null>(null);
//   const fileInputRef = useRef<HTMLInputElement | null>(null);

//   // 后端API地址
//   const backendUrl = 'http://127.0.0.1:8000';
// // ==============================================================================
// // 完整 App.tsx - 第二部分: 核心逻辑函数
// // ==============================================================================

//   const onSelectFile = (e: React.ChangeEvent<HTMLInputElement>) => {
//     if (e.target.files && e.target.files.length > 0) {
//       setSolution('');
//       setError('');
//       setSolvedImageSrc('');
//       setProgress(0);
//       setStatusText('');
//       setCrop(undefined);
//       fileRef.current = e.target.files[0];
//       const reader = new FileReader();
//       reader.addEventListener('load', () => setImgSrc(reader.result?.toString() || ''));
//       reader.readAsDataURL(fileRef.current);
//     }
//   };

//   const sendRequest = async (imageBlob: Blob | File, imageSrcForDisplay: string) => {
//     setIsLoading(true);
//     setSolution('');
//     setError('');
//     setSolvedImageSrc(imageSrcForDisplay);
    
//     let progressInterval: number | null = null;
//     try {
//       setProgress(10);
//       setStatusText('正在上传并进行图像内容识别 (OCR & Vision)...');
//       await new Promise(resolve => setTimeout(resolve, 1500)); 
//       setProgress(40);

//       setStatusText('AI导师正在进行深度推理与解答...');
      
//       const formData = new FormData();
//       formData.append('file', imageBlob, 'image-to-solve.png');

//       const responsePromise = axios.post<{ solution: string }>(`${backendUrl}/solve`, formData);

//       progressInterval = window.setInterval(() => {
//           setProgress(p => (p < 90 ? p + 2 : p));
//       }, 200);

//       const response = await responsePromise;
//       if(progressInterval) clearInterval(progressInterval);

//       setProgress(100);
//       setStatusText('解答生成完毕！');
      
//       // --- 调用新的终极格式化函数 ---
//       const finalFormattedSolution = finalFormatAIResponse(response.data.solution);
//       setSolution(finalFormattedSolution);

//     } catch (err) {
//       if(progressInterval) clearInterval(progressInterval);
//       setError('糟糕，出错了！可能是图片无法识别或服务器繁忙。');
//       console.error("Axios 请求错误:", err);
//       setProgress(0);
//     } finally {
//       setTimeout(() => {
//         setIsLoading(false);
//         if (fileInputRef.current) fileInputRef.current.value = "";
//       }, 1500);
//     }
//   }

//   const handleSolveCroppedImage = () => {
//     if (!crop || !imgRef.current || !crop.width || !crop.height) {
//       setError('请先在图片上拖动以选择一个裁剪区域。');
//       return;
//     }
//     const canvas = document.createElement('canvas');
//     const scaleX = imgRef.current.naturalWidth / imgRef.current.width;
//     const scaleY = imgRef.current.naturalHeight / imgRef.current.height;
//     canvas.width = Math.floor(crop.width * scaleX);
//     canvas.height = Math.floor(crop.height * scaleY);
//     const ctx = canvas.getContext('2d');
//     if (!ctx) {
//       setError('无法处理图片，浏览器支持不足。');
//       return;
//     }
//     ctx.drawImage(imgRef.current, crop.x * scaleX, crop.y * scaleY, crop.width * scaleX, crop.height * scaleY, 0, 0, canvas.width, canvas.height);
//     canvas.toBlob((blob) => {
//       if (blob) sendRequest(blob, canvas.toDataURL('image/png'));
//       else setError('无法生成裁剪后的图片。');
//     }, 'image/png');
//   };

//   const handleSolveOriginalImage = () => {
//     if (fileRef.current && imgSrc) {
//       sendRequest(fileRef.current, imgSrc);
//     } else {
//       setError('找不到原始图片文件，请重新上传。');
//     }
//   }
  
//   const handleCancelCrop = () => {
//     setImgSrc('');
//     setError('');
//     setSolution('');
//     setSolvedImageSrc('');
//     setProgress(0);
//     setStatusText('');
//     fileRef.current = null;
//   }
// // ==============================================================================
// // 完整 App.tsx - 第三部分: UI渲染 (JSX)
// // ==============================================================================

//   return (
//     <div className="App">
//       <header className="App-header">
//         <h1>AI 拍照解题</h1>
//         <p>上传题目图片，裁剪或直接解答！</p>
//       </header>
//       <main className="App-main">
//         {isLoading && (
//             <div className="status-container card-container">
//                 <div className="status-text">{statusText}</div>
//                 <div className="progress-bar">
//                     <div className="progress-bar-inner" style={{ width: `${progress}%` }}></div>
//                 </div>
//             </div>
//         )}

//         {error && <div className="error">{error}</div>}

//         {solution && (
//           <div className="solution-container card-container">
//             {solvedImageSrc && (
//               <div className="solved-image-container">
//                 <h3>题目原文</h3>
//                 <img src={solvedImageSrc} alt="已解答的题目" className="solved-image" />
//               </div>
//             )}
//             <h2>解题详情：</h2>
//             <ReactMarkdown
//               children={solution}
//               remarkPlugins={[remarkMath]}
//               rehypePlugins={[rehypeKatex]}
//             />
//           </div>
//         )}

//         {!isLoading && !solution && (
//           <div className="card-container">
//             {!imgSrc ? (
//               <div className="upload-container" onClick={() => fileInputRef.current?.click()}>
//                 <input ref={fileInputRef} id="file-input" type="file" accept="image/*" onChange={onSelectFile} style={{ display: 'none' }} />
//                 <div className="upload-text">点击或拖拽图片到此区域</div>
//                 <div className="upload-button">选择文件</div>
//               </div>
//             ) : (
//               <div className="crop-container">
//                 <ReactCrop crop={crop} onChange={c => setCrop(c)}>
//                   <img ref={imgRef} src={imgSrc} alt="Crop preview" />
//                 </ReactCrop>
//                 <div className="crop-actions">
//                   <button onClick={handleSolveOriginalImage} className="solve-direct-btn">直接解答</button>
//                   <button onClick={handleSolveCroppedImage} disabled={!crop?.width || !crop?.height} className="solve-crop-btn">解答裁剪区域</button>
//                   <button onClick={handleCancelCrop} className="cancel-btn">重新上传</button>
//                 </div>
//               </div>
//             )}
//           </div>
//         )}
//       </main>
//     </div>
//   );
// }

// export default App;

// ==============================================================================
// 完整 App.tsx - 【V8.2 终极分治格式化版】
// ==============================================================================

// ==============================================================================
// 完整 App.tsx - 【V9.0 终极渲染版】
// ==============================================================================

import React, { useState, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import './App.css';

// 导入裁剪库的组件和类型
import ReactCrop, { type Crop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';


// --- 【V9.0 终极分治版】的格式化函数 ---
function finalFormatAIResponse(text: string): string {
    // 预处理
    let processedText = text.replace(/### 解题详情：|### 题目解答|### 解题步骤|好的，同学，我们一起来看这个问题。|好的，同学，我们一起来解决这个问题。/gi, '').trim();

    // 步骤1: 使用$$...$$和$...$作为“安全岛”，将文本分割
    // 这个正则表达式会匹配所有正确格式的块级或行内公式，并将它们作为分隔符
    const parts = processedText.split(/(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$)/g);

    const formattedParts = parts.map((part, index) => {
        // 如果当前部分是已经被正确标记的公式 (分隔符本身)，原样返回
        if (part.startsWith('$') && part.endsWith('$')) {
            return part;
        }

        // --- 只对普通文本段落进行处理 ---
        let textPart = part;

        // 规则A: 智能处理括号
        textPart = textPart.replace(/(?<!\\)\(([\s\S]*?)(?<!\\)\)/g, (match, content) => {
            const cleanContent = content.trim();
            // 如果括号内已经有$，或者内容为空，或者包含中文长句，则不处理
            if (cleanContent === '' || /[\u4e00-\u9fa5]/.test(cleanContent) || cleanContent.split(' ').length > 6) {
                return match;
            }
            return `$${cleanContent}$`;
        });
        
        // 规则B: 处理 \[ ... \]
        textPart = textPart.replace(/\\\[([\s\S]*?)\\\]/g, '$$$$$1$$$$');

        return textPart;
    });

    // 步骤2: 重新拼接
    processedText = formattedParts.join('');

    // 步骤3: 最终清理：处理Markdown转义问题
    // 在所有公式内部，将单个 \ 替换为 \\
    processedText = processedText.replace(/(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$)/g, (match) => {
        return match.replace(/\\/g, '\\\\');
    });

    return processedText;
}


// 主应用组件
function App() {
  // --- 状态定义 ---
  const [solution, setSolution] = useState<string>('');
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
    setSolution('');
    setError('');
    setSolvedImageSrc(imageSrcForDisplay);
    
    let progressInterval: number | null = null;
    try {
      setProgress(10);
      setStatusText('正在上传并进行图像内容识别...');
      
      const formData = new FormData();
      formData.append('file', imageBlob, 'image-to-solve.png');

      await new Promise(resolve => setTimeout(resolve, 1500)); 
      setProgress(40);
      setStatusText('AI导师正在进行深度推理与解答...');

      progressInterval = window.setInterval(() => {
          setProgress(p => (p < 90 ? p + 2 : p));
      }, 200);

      const response = await axios.post<{ solution: string }>(`${backendUrl}/solve`, formData);
      
      if(progressInterval) clearInterval(progressInterval);
      setProgress(100);
      setStatusText('解答生成完毕！');
      
      // --- 调用新的终极格式化函数 ---
      const finalFormattedSolution = finalFormatAIResponse(response.data.solution);
      setSolution(finalFormattedSolution);

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

        {solution && (
          <div className="solution-container card-container">
            {solvedImageSrc && (
              <div className="solved-image-container">
                <h3>题目原文</h3>
                <img src={solvedImageSrc} alt="已解答的题目" className="solved-image" />
              </div>
            )}
            <h2>解题详情：</h2>
            <ReactMarkdown
              children={solution}
              remarkPlugins={[remarkMath]}
              rehypePlugins={[rehypeKatex]}
            />
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