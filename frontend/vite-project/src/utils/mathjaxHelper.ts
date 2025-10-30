/**
 * ==============================================================================
 * MathJax 渲染辅助工具
 * ==============================================================================
 * 功能：
 * 1. 智能等待 MathJax 加载完成
 * 2. 自动重试渲染失败的公式
 * 3. 检测未渲染的 LaTeX 源代码并重新渲染
 * 4. 提供渲染进度日志
 * ==============================================================================
 */

declare global {
  interface Window {
    MathJax: any;
  }
}

/**
 * 等待 MathJax 完全加载
 * @param maxWait 最大等待时间（毫秒）
 * @returns Promise<boolean> 是否加载成功
 */
export async function waitForMathJax(maxWait: number = 10000): Promise<boolean> {
  const startTime = Date.now();
  
  while (Date.now() - startTime < maxWait) {
    if (window.MathJax && window.MathJax.typesetPromise) {
      console.log('✅ [MathJax辅助] MathJax 已加载完成');
      return true;
    }
    
    // 每100ms检查一次
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  console.error('❌ [MathJax辅助] MathJax 加载超时');
  return false;
}

/**
 * 检测页面中是否有未渲染的 LaTeX 源代码
 * @param container 要检查的容器（默认整个文档）
 * @returns 未渲染的公式数量
 */
export function detectUnrenderedLatex(container?: HTMLElement): number {
  const target = container || document.body;
  const text = target.textContent || '';
  
  // 检测常见的 LaTeX 模式
  const patterns = [
    /\$\$.+?\$\$/g,           // 独立公式 $$...$$
    /\$[^$]+?\$/g,            // 行内公式 $...$
    /\\\[.+?\\\]/g,           // \[...\]
    /\\\(.+?\\\)/g,           // \(...\)
    /\\frac\{/g,              // \frac{
    /\\sqrt\{/g,              // \sqrt{
    /\\sum_/g,                // \sum_
    /\\int_/g,                // \int_
  ];
  
  let unrenderedCount = 0;
  
  for (const pattern of patterns) {
    const matches = text.match(pattern);
    if (matches) {
      unrenderedCount += matches.length;
    }
  }
  
  if (unrenderedCount > 0) {
    console.warn(`⚠️ [MathJax辅助] 检测到 ${unrenderedCount} 个可能未渲染的 LaTeX 公式`);
  }
  
  return unrenderedCount;
}

/**
 * 智能渲染 MathJax 公式（带重试机制）
 * @param container 要渲染的容器（可选）
 * @param maxRetries 最大重试次数
 * @param retryDelay 重试延迟（毫秒）
 */
export async function renderMathJaxWithRetry(
  container?: HTMLElement | HTMLElement[],
  maxRetries: number = 3,
  retryDelay: number = 500
): Promise<void> {
  // 等待 MathJax 加载
  const isLoaded = await waitForMathJax();
  if (!isLoaded) {
    console.error('❌ [MathJax辅助] MathJax 未加载，无法渲染公式');
    return;
  }
  
  let attempt = 0;
  let lastUnrenderedCount = Infinity;
  
  while (attempt < maxRetries) {
    attempt++;
    
    try {
      console.log(`🔄 [MathJax辅助] 开始第 ${attempt} 次渲染尝试...`);
      
      // 执行渲染
      if (container) {
        await window.MathJax.typesetPromise(Array.isArray(container) ? container : [container]);
      } else {
        await window.MathJax.typesetPromise();
      }
      
      console.log(`✅ [MathJax辅助] 第 ${attempt} 次渲染完成`);
      
      // 等待一小段时间让 DOM 更新
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // 检测是否还有未渲染的公式
      const targetElement = container 
        ? (Array.isArray(container) ? container[0] : container)
        : undefined;
      const unrenderedCount = detectUnrenderedLatex(targetElement);
      
      // 如果没有未渲染的公式，或者数量不再减少，则结束
      if (unrenderedCount === 0) {
        console.log('✅ [MathJax辅助] 所有公式已成功渲染');
        return;
      } else if (unrenderedCount >= lastUnrenderedCount) {
        console.warn(`⚠️ [MathJax辅助] 仍有 ${unrenderedCount} 个公式未渲染，但数量不再减少`);
        if (attempt >= maxRetries) {
          console.error('❌ [MathJax辅助] 已达到最大重试次数，仍有公式未渲染');
          return;
        }
      }
      
      lastUnrenderedCount = unrenderedCount;
      
      // 如果还有未渲染的公式且未达到最大重试次数，等待后重试
      if (attempt < maxRetries) {
        console.log(`⏳ [MathJax辅助] ${retryDelay}ms 后进行第 ${attempt + 1} 次重试...`);
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
      
    } catch (err) {
      console.error(`❌ [MathJax辅助] 第 ${attempt} 次渲染失败:`, err);
      
      if (attempt < maxRetries) {
        console.log(`⏳ [MathJax辅助] ${retryDelay}ms 后进行第 ${attempt + 1} 次重试...`);
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      } else {
        throw err;
      }
    }
  }
}

/**
 * 启动 MathJax 自动监控器
 * 定期检查页面中的未渲染公式并自动渲染
 * @param interval 检查间隔（毫秒）
 * @returns 停止监控的函数
 */
export function startMathJaxMonitor(interval: number = 2000): () => void {
  let isMonitoring = true;
  
  async function monitor() {
    while (isMonitoring) {
      try {
        // 检测未渲染的公式
        const unrenderedCount = detectUnrenderedLatex();
        
        // 如果有未渲染的公式，尝试渲染
        if (unrenderedCount > 0) {
          console.log(`🔍 [MathJax监控] 发现 ${unrenderedCount} 个未渲染公式，开始渲染...`);
          await renderMathJaxWithRetry(undefined, 2, 300);
        }
      } catch (err) {
        console.error('❌ [MathJax监控] 监控过程出错:', err);
      }
      
      // 等待下一次检查
      await new Promise(resolve => setTimeout(resolve, interval));
    }
  }
  
  // 启动监控
  monitor();
  console.log(`🚀 [MathJax监控] 已启动，检查间隔: ${interval}ms`);
  
  // 返回停止函数
  return () => {
    isMonitoring = false;
    console.log('🛑 [MathJax监控] 已停止');
  };
}

/**
 * 简化的渲染函数（推荐使用）
 * 自动处理延迟和重试
 */
export async function renderMathJax(
  container?: HTMLElement | HTMLElement[],
  delay: number = 500
): Promise<void> {
  // 延迟一段时间，确保 DOM 已更新
  await new Promise(resolve => setTimeout(resolve, delay));
  
  // 使用重试机制渲染
  await renderMathJaxWithRetry(container, 3, 500);
}

