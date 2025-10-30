/**
 * ==============================================================================
 * TextItem - 简单文本渲染组件（支持LaTeX和Markdown）
 * ==============================================================================
 * 用于渲染简单的文本内容，比QuestionItem更轻量
 */

import React, { useEffect, useRef } from 'react';
import { marked } from 'marked';

// 配置marked以保护LaTeX公式
marked.setOptions({
  breaks: true,
  gfm: true,
  pedantic: false,
  sanitize: false,
  smartLists: true,
  smartypants: false, // 关键：不要转换引号和破折号
});

declare global {
  interface Window {
    MathJax: any;
  }
}

interface TextItemProps {
  content: string;
}

const TextItem: React.FC<TextItemProps> = ({ content }) => {
  const contentRef = useRef<HTMLDivElement>(null);

  // 触发MathJax渲染
  useEffect(() => {
    const renderMath = async () => {
      if (!window.MathJax || !window.MathJax.typesetPromise) {
        console.warn('⚠️ [TextItem] MathJax未加载完成');
        return;
      }

      try {
        if (contentRef.current) {
          console.log('🔄 [TextItem] 开始MathJax渲染');
          await window.MathJax.typesetPromise([contentRef.current]);
          console.log('✅ [TextItem] MathJax渲染成功');
        }
      } catch (err) {
        console.error('❌ [TextItem] MathJax渲染失败:', err);
      }
    };

    const timer = setTimeout(renderMath, 150);
    return () => clearTimeout(timer);
  }, [content]);

  if (!content) {
    return <div style={{ color: '#999', fontStyle: 'italic' }}>（无内容）</div>;
  }

  // 简单处理换行，不使用marked.parse（避免破坏LaTeX公式）
  const formattedContent = content.replace(/\n/g, '<br/>');

  return (
    <div
      ref={contentRef}
      className="math-content"
      style={{
        whiteSpace: 'pre-wrap',
        lineHeight: '1.6'
      }}
      dangerouslySetInnerHTML={{ __html: formattedContent }}
    />
  );
};

export default TextItem;

