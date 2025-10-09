// ==============================================================================
// QuestionSelector.tsx - 【V24.0 题目分页选择器组件】
// 功能：在整页多题模式下，提供题目切换的Tab式界面
// ==============================================================================

import React from 'react';
import './QuestionSelector.css';

interface QuestionSelectorProps {
  count: number;           // 题目总数
  activeIndex: number;     // 当前激活的题目索引
  onSelect: (index: number) => void;  // 切换题目的回调函数
  loadingStates?: boolean[];  // 可选：每个题目的加载状态
  errorStates?: boolean[];    // 可选：每个题目的错误状态
}

const QuestionSelector: React.FC<QuestionSelectorProps> = ({ 
  count, 
  activeIndex, 
  onSelect,
  loadingStates = [],
  errorStates = []
}) => {
  return (
    <div className="question-selector">
      <div className="question-selector-header">
        <span className="selector-title">📋 题目导航</span>
        <span className="selector-count">共 {count} 题</span>
      </div>
      
      <div className="question-tabs-container">
        {Array.from({ length: count }, (_, i) => {
          const isActive = i === activeIndex;
          const isLoading = loadingStates[i] || false;
          const hasError = errorStates[i] || false;
          
          let statusIcon = '';
          let statusClass = '';
          
          if (isLoading) {
            statusIcon = '⏳';
            statusClass = 'loading';
          } else if (hasError) {
            statusIcon = '❌';
            statusClass = 'error';
          } else {
            statusIcon = '✓';
            statusClass = 'completed';
          }
          
          return (
            <button
              key={i}
              className={`question-tab ${isActive ? 'active' : ''} ${statusClass}`}
              onClick={() => onSelect(i)}
              title={`第 ${i + 1} 题${isLoading ? ' - 处理中' : hasError ? ' - 出错' : ''}`}
            >
              <span className="tab-number">{i + 1}</span>
              {!isActive && <span className="tab-status-icon">{statusIcon}</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default QuestionSelector;

