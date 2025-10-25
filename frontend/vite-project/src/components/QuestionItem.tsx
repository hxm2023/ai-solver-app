// ==============================================================================
// QuestionItem.tsx - 单个题目组件（修复LaTeX渲染Bug）
// 核心功能：
// 1. 独立的MathJax渲染逻辑
// 2. 确保每个题目挂载时都能正确触发LaTeX渲染
// 3. 支持SVG图表和Markdown表格显示
// ==============================================================================

import React, { useEffect, useRef } from 'react';
import { marked } from 'marked';

interface Question {
  id: string;
  content: string;
  answer: string;
  explanation: string;
  knowledge_points: string[];
  difficulty: string;
  created_at: string;
}

interface QuestionItemProps {
  question: Question;
  index: number;
  isSelected: boolean;
  onToggleSelect: (questionId: string) => void;
  onDelete: (questionId: string) => void;
  onExportPDF: (questionIds: string[]) => void;
}

const QuestionItem: React.FC<QuestionItemProps> = ({
  question,
  index,
  isSelected,
  onToggleSelect,
  onDelete,
  onExportPDF
}) => {
  // 为每个部分创建独立的引用
  const contentRef = useRef<HTMLDivElement>(null);
  const answerRef = useRef<HTMLSpanElement>(null);
  const explanationRef = useRef<HTMLDivElement>(null);

  // 【关键功能】当题目内容变化时，触发MathJax渲染
  useEffect(() => {
    const renderMath = async () => {
      // 检查MathJax是否可用
      if (!window.MathJax || !window.MathJax.typesetPromise) {
        console.warn('MathJax未加载完成');
        return;
      }

      try {
        // 收集所有需要渲染的DOM元素
        const elements: HTMLElement[] = [];
        if (contentRef.current) elements.push(contentRef.current);
        if (answerRef.current) elements.push(answerRef.current);
        if (explanationRef.current) elements.push(explanationRef.current);

        // 只渲染这个题目相关的元素，避免全局渲染
        if (elements.length > 0) {
          await window.MathJax.typesetPromise(elements);
        }
      } catch (err) {
        console.error(`题目${index + 1} MathJax渲染失败:`, err);
      }
    };

    // 延迟渲染，确保DOM已完全更新
    const timer = setTimeout(renderMath, 100);
    return () => clearTimeout(timer);
  }, [question.content, question.answer, question.explanation, index]);

  // 安全的Markdown解析函数
  const parseMarkdown = (text: string): string => {
    try {
      return marked.parse(text) as string;
    } catch (err) {
      console.error('Markdown解析失败:', err);
      // 降级处理：简单的换行转换
      return text.replace(/\n/g, '<br/>');
    }
  };

  return (
    <div
      style={{
        border: isSelected ? '2px solid #5C6AC4' : '1px solid #ddd',
        borderRadius: '10px',
        padding: '20px',
        background: isSelected ? '#f5f7ff' : 'white',
        transition: 'all 0.2s'
      }}
    >
      {/* 题目头部 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '15px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onToggleSelect(question.id)}
            style={{
              width: '18px',
              height: '18px',
              cursor: 'pointer'
            }}
          />
          <h4 style={{ margin: 0 }}>题目 {index + 1}</h4>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <span style={{
            background: '#FFC107',
            color: 'white',
            padding: '4px 12px',
            borderRadius: '12px',
            fontSize: '12px'
          }}>
            {question.difficulty}
          </span>
          <button
            onClick={() => onExportPDF([question.id])}
            style={{
              padding: '4px 12px',
              background: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            📥 PDF
          </button>
          <button
            onClick={() => onDelete(question.id)}
            style={{
              padding: '4px 12px',
              background: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            🗑️ 删除
          </button>
        </div>
      </div>

      {/* 题目内容 - 使用独立ref确保MathJax渲染 */}
      <div
        ref={contentRef}
        style={{
          background: '#f9f9f9',
          padding: '15px',
          borderRadius: '8px',
          marginBottom: '15px',
          whiteSpace: 'pre-wrap',
          lineHeight: '1.8'
        }}
        className="math-content"
        dangerouslySetInnerHTML={{ __html: parseMarkdown(question.content) }}
      />

      {/* 答案 */}
      <div style={{ marginBottom: '10px' }}>
        <strong style={{ color: '#4CAF50' }}>答案：</strong>
        <span
          ref={answerRef}
          style={{ marginLeft: '10px' }}
          className="math-content"
          dangerouslySetInnerHTML={{ __html: parseMarkdown(question.answer) }}
        />
      </div>

      {/* 解析 */}
      {question.explanation && (
        <div style={{ marginBottom: '10px' }}>
          <strong style={{ color: '#FF9800' }}>解析：</strong>
          <div
            ref={explanationRef}
            className="math-content"
            style={{
              marginTop: '8px',
              padding: '12px',
              background: '#fff3e0',
              borderRadius: '6px',
              fontSize: '14px',
              whiteSpace: 'pre-wrap',
              lineHeight: '1.8'
            }}
            dangerouslySetInnerHTML={{ __html: parseMarkdown(question.explanation) }}
          />
        </div>
      )}

      {/* 知识点标签 */}
      {question.knowledge_points.length > 0 && (
        <div>
          <strong>知识点：</strong>
          {question.knowledge_points.map((kp, idx) => (
            <span
              key={idx}
              style={{
                display: 'inline-block',
                background: '#e3f2fd',
                padding: '4px 10px',
                borderRadius: '4px',
                fontSize: '12px',
                marginLeft: '8px',
                marginTop: '5px'
              }}
            >
              {kp}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default QuestionItem;

