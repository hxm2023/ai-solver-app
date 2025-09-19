import React from 'react';
import './ModeSelector.css'; // 我们稍后会创建这个CSS文件

// 定义这个组件接收的props类型
interface ModeSelectorProps {
  onSelectMode: (mode: 'solve' | 'review') => void;
}

const ModeSelector: React.FC<ModeSelectorProps> = ({ onSelectMode }) => {
  return (
    <div className="mode-selector-container">
      <div className="mode-selector-card">
        <h1 className="mode-selector-title">请选择功能模式</h1>
        <p className="mode-selector-subtitle">
          你想让AI为你解答难题，还是批改你的作业？
        </p>
        <div className="mode-buttons">
          <button
            className="mode-button solve-button"
            onClick={() => onSelectMode('solve')}
          >
            <span className="button-icon">🧠</span>
            <span className="button-text">AI 智能解题</span>
            <span className="button-description">上传题目，获取详细解答</span>
          </button>
          <button
            className="mode-button review-button"
            onClick={() => onSelectMode('review')}
          >
            <span className="button-icon">📝</span>
            <span className="button-text">AI 批改作业</span>
            <span className="button-description">上传题目和你的答案，获取专业点评</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModeSelector;