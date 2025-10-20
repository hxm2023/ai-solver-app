// ==============================================================================
// PersonalLearning.tsx - 个性化学习系统界面 (Feature 2/3/4)
// 功能：错题本、智能出题、试卷生成
// ==============================================================================

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './PersonalLearning.css';

const API_BASE_URL = 'http://127.0.0.1:8000';

// 获取Token
const getToken = () => localStorage.getItem('auth_token');
const getAuthHeaders = () => ({
  'Authorization': `Bearer ${getToken()}`,
  'Content-Type': 'application/json'
});

// ==============================================================================
// 1. 错题本界面
// ==============================================================================
interface Mistake {
  id: number;
  question_text: string;
  wrong_answer: string | null;
  ai_analysis: string;
  subject: string | null;
  difficulty: number | null;
  reviewed: boolean;
  review_count: number;
  created_at: string;
  has_image: boolean;
}

const MistakeBookTab: React.FC = () => {
  const [mistakes, setMistakes] = useState<Mistake[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [filter, setFilter] = useState({ subject: '', reviewed: 'all' });

  useEffect(() => {
    loadMistakes();
    loadStats();
  }, []);

  const loadMistakes = async () => {
    setLoading(true);
    try {
      const params: any = { page: 1, page_size: 20 };
      if (filter.subject) params.subject = filter.subject;
      if (filter.reviewed !== 'all') params.reviewed = filter.reviewed === 'true';

      const response = await axios.get(`${API_BASE_URL}/mistakes/`, {
        headers: getAuthHeaders(),
        params
      });
      setMistakes(response.data.mistakes);
    } catch (error: any) {
      alert('加载错题失败：' + (error.response?.data?.detail || '网络错误'));
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/mistakes/stats/summary`, {
        headers: getAuthHeaders()
      });
      setStats(response.data);
    } catch (error) {
      console.error('加载统计失败', error);
    }
  };

  const markAsReviewed = async (id: number) => {
    try {
      await axios.put(`${API_BASE_URL}/mistakes/${id}`, 
        { reviewed: true },
        { headers: getAuthHeaders() }
      );
      alert('已标记为已复习！');
      loadMistakes();
      loadStats();
    } catch (error: any) {
      alert('操作失败：' + (error.response?.data?.detail || '网络错误'));
    }
  };

  const deleteMistake = async (id: number) => {
    if (!confirm('确定要删除这道错题吗？')) return;
    try {
      await axios.delete(`${API_BASE_URL}/mistakes/${id}`, {
        headers: getAuthHeaders()
      });
      alert('删除成功！');
      loadMistakes();
      loadStats();
    } catch (error: any) {
      alert('删除失败：' + (error.response?.data?.detail || '网络错误'));
    }
  };

  return (
    <div className="mistake-book-tab">
      <h2>📚 我的错题本</h2>

      {/* 统计卡片 */}
      {stats && (
        <div className="stats-cards">
          <div className="stat-card">
            <div className="stat-number">{stats.total}</div>
            <div className="stat-label">总错题数</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.reviewed}</div>
            <div className="stat-label">已复习</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.not_reviewed}</div>
            <div className="stat-label">未复习</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{stats.review_progress}%</div>
            <div className="stat-label">复习进度</div>
          </div>
        </div>
      )}

      {/* 筛选栏 */}
      <div className="filter-bar">
        <select 
          value={filter.subject}
          onChange={(e) => setFilter({...filter, subject: e.target.value})}
        >
          <option value="">全部学科</option>
          <option value="数学">数学</option>
          <option value="物理">物理</option>
          <option value="化学">化学</option>
          <option value="英语">英语</option>
        </select>

        <select 
          value={filter.reviewed}
          onChange={(e) => setFilter({...filter, reviewed: e.target.value})}
        >
          <option value="all">全部状态</option>
          <option value="false">未复习</option>
          <option value="true">已复习</option>
        </select>

        <button onClick={loadMistakes} className="btn-primary">
          🔍 筛选
        </button>
      </div>

      {/* 错题列表 */}
      {loading ? (
        <div className="loading">加载中...</div>
      ) : mistakes.length === 0 ? (
        <div className="empty-state">
          <p>📝 还没有错题哦~</p>
          <p>做错题后会自动保存到这里</p>
        </div>
      ) : (
        <div className="mistake-list">
          {mistakes.map((mistake) => (
            <div key={mistake.id} className={`mistake-card ${mistake.reviewed ? 'reviewed' : ''}`}>
              <div className="mistake-header">
                <span className="mistake-subject">{mistake.subject || '未分类'}</span>
                <span className="mistake-status">
                  {mistake.reviewed ? '✅ 已复习' : '❌ 未复习'}
                </span>
                {mistake.difficulty && (
                  <span className="mistake-difficulty">难度: {mistake.difficulty}/5</span>
                )}
              </div>

              <div className="mistake-question">
                <strong>题目：</strong>
                {mistake.question_text.substring(0, 100)}
                {mistake.question_text.length > 100 ? '...' : ''}
              </div>

              {mistake.wrong_answer && (
                <div className="mistake-answer">
                  <strong>错误答案：</strong>{mistake.wrong_answer}
                </div>
              )}

              <div className="mistake-analysis">
                <strong>AI分析：</strong>
                {mistake.ai_analysis.substring(0, 150)}
                {mistake.ai_analysis.length > 150 ? '...' : ''}
              </div>

              <div className="mistake-actions">
                <button 
                  onClick={() => markAsReviewed(mistake.id)}
                  disabled={mistake.reviewed}
                  className="btn-secondary"
                >
                  📖 标记已复习
                </button>
                <button 
                  onClick={() => deleteMistake(mistake.id)}
                  className="btn-danger"
                >
                  🗑️ 删除
                </button>
              </div>

              <div className="mistake-meta">
                创建时间: {new Date(mistake.created_at).toLocaleString()} | 
                复习次数: {mistake.review_count}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ==============================================================================
// 2. 智能出题界面
// ==============================================================================
const QuestionGeneratorTab: React.FC = () => {
  const [step, setStep] = useState<'select' | 'knowledge' | 'generate' | 'result'>('select');
  const [mistakes, setMistakes] = useState<Mistake[]>([]);
  const [selectedMistakes, setSelectedMistakes] = useState<number[]>([]);
  const [knowledgePoints, setKnowledgePoints] = useState<string[]>([]);
  const [selectedKnowledge, setSelectedKnowledge] = useState<string[]>([]);
  const [difficulty, setDifficulty] = useState('中等');
  const [questionTypes, setQuestionTypes] = useState({ '选择题': 2, '填空题': 1 });
  const [generatedQuestions, setGeneratedQuestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadMistakes();
  }, []);

  const loadMistakes = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/mistakes/`, {
        headers: getAuthHeaders(),
        params: { page: 1, page_size: 50 }
      });
      setMistakes(response.data.mistakes);
    } catch (error) {
      alert('加载错题失败');
    }
  };

  const generateKnowledgePoints = async () => {
    if (selectedMistakes.length === 0) {
      alert('请至少选择一道错题');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/ai-learning/generate_knowledge_points`,
        { mistake_ids: selectedMistakes, subject: '数学' },
        { headers: getAuthHeaders() }
      );
      setKnowledgePoints(response.data.knowledge_points);
      setSelectedKnowledge(response.data.knowledge_points); // 默认全选
      setStep('knowledge');
    } catch (error: any) {
      alert('提炼知识点失败：' + (error.response?.data?.detail || '网络错误'));
    } finally {
      setLoading(false);
    }
  };

  const generateQuestions = async () => {
    if (selectedKnowledge.length === 0) {
      alert('请至少选择一个知识点');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/ai-learning/generate_questions`,
        {
          knowledge_points: selectedKnowledge,
          difficulty: difficulty,
          question_types: questionTypes,
          subject: '数学'
        },
        { headers: getAuthHeaders() }
      );
      setGeneratedQuestions(response.data.questions);
      setStep('result');
    } catch (error: any) {
      alert('生成题目失败：' + (error.response?.data?.detail || '网络错误'));
    } finally {
      setLoading(false);
    }
  };

  const toggleMistakeSelection = (id: number) => {
    setSelectedMistakes(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const toggleKnowledgeSelection = (kp: string) => {
    setSelectedKnowledge(prev => 
      prev.includes(kp) ? prev.filter(x => x !== kp) : [...prev, kp]
    );
  };

  return (
    <div className="question-generator-tab">
      <h2>🎯 智能出题</h2>

      {/* 步骤指示器 */}
      <div className="steps-indicator">
        <div className={`step ${step === 'select' ? 'active' : ''}`}>1. 选择错题</div>
        <div className={`step ${step === 'knowledge' ? 'active' : ''}`}>2. 选择知识点</div>
        <div className={`step ${step === 'generate' ? 'active' : ''}`}>3. 设置参数</div>
        <div className={`step ${step === 'result' ? 'active' : ''}`}>4. 查看结果</div>
      </div>

      {/* 步骤1：选择错题 */}
      {step === 'select' && (
        <div className="step-content">
          <h3>请选择要分析的错题（可多选）</h3>
          {mistakes.length === 0 ? (
            <div className="empty-state">
              <p>还没有错题</p>
              <p>请先去错题本添加错题</p>
            </div>
          ) : (
            <div className="selectable-list">
              {mistakes.map((mistake) => (
                <div 
                  key={mistake.id}
                  className={`selectable-item ${selectedMistakes.includes(mistake.id) ? 'selected' : ''}`}
                  onClick={() => toggleMistakeSelection(mistake.id)}
                >
                  <input 
                    type="checkbox" 
                    checked={selectedMistakes.includes(mistake.id)}
                    readOnly
                  />
                  <div>
                    <div className="item-title">{mistake.question_text.substring(0, 60)}...</div>
                    <div className="item-meta">{mistake.subject} | {mistake.created_at}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="step-actions">
            <button 
              onClick={generateKnowledgePoints}
              disabled={selectedMistakes.length === 0 || loading}
              className="btn-primary btn-large"
            >
              {loading ? '正在分析...' : `🧠 分析已选错题 (${selectedMistakes.length}道)`}
            </button>
          </div>
        </div>
      )}

      {/* 步骤2：选择知识点 */}
      {step === 'knowledge' && (
        <div className="step-content">
          <h3>AI为你提炼了以下知识点</h3>
          <div className="knowledge-points-list">
            {knowledgePoints.map((kp, index) => (
              <div 
                key={index}
                className={`knowledge-point ${selectedKnowledge.includes(kp) ? 'selected' : ''}`}
                onClick={() => toggleKnowledgeSelection(kp)}
              >
                <input 
                  type="checkbox" 
                  checked={selectedKnowledge.includes(kp)}
                  readOnly
                />
                <span>{kp}</span>
              </div>
            ))}
          </div>
          <div className="step-actions">
            <button onClick={() => setStep('select')} className="btn-secondary">
              ← 返回
            </button>
            <button 
              onClick={() => setStep('generate')}
              disabled={selectedKnowledge.length === 0}
              className="btn-primary"
            >
              下一步：设置参数 →
            </button>
          </div>
        </div>
      )}

      {/* 步骤3：设置参数 */}
      {step === 'generate' && (
        <div className="step-content">
          <h3>设置生成参数</h3>
          
          <div className="param-section">
            <label>难度：</label>
            <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
              <option value="简单">简单</option>
              <option value="中等">中等</option>
              <option value="困难">困难</option>
            </select>
          </div>

          <div className="param-section">
            <label>选择题数量：</label>
            <input 
              type="number" 
              min="0" 
              max="10"
              value={questionTypes['选择题']}
              onChange={(e) => setQuestionTypes({...questionTypes, '选择题': parseInt(e.target.value) || 0})}
            />
          </div>

          <div className="param-section">
            <label>填空题数量：</label>
            <input 
              type="number" 
              min="0" 
              max="10"
              value={questionTypes['填空题']}
              onChange={(e) => setQuestionTypes({...questionTypes, '填空题': parseInt(e.target.value) || 0})}
            />
          </div>

          <div className="step-actions">
            <button onClick={() => setStep('knowledge')} className="btn-secondary">
              ← 返回
            </button>
            <button 
              onClick={generateQuestions}
              disabled={loading}
              className="btn-primary btn-large"
            >
              {loading ? '正在生成题目...' : '🎲 开始生成'}
            </button>
          </div>
        </div>
      )}

      {/* 步骤4：查看结果 */}
      {step === 'result' && (
        <div className="step-content">
          <h3>✅ 生成完成！共 {generatedQuestions.length} 道题目</h3>
          <div className="generated-questions">
            {generatedQuestions.map((q, index) => {
              const content = JSON.parse(q.content);
              return (
                <div key={index} className="generated-question">
                  <div className="question-header">
                    <span className="question-number">题目 {index + 1}</span>
                    <span className="question-type">{q.question_type}</span>
                    <span className="question-difficulty">{q.difficulty}</span>
                  </div>
                  <div className="question-stem">
                    <strong>题干：</strong>{content.stem}
                  </div>
                  {content.options && (
                    <div className="question-options">
                      {Object.entries(content.options).map(([key, value]: [string, any]) => (
                        <div key={key}>{key}. {value}</div>
                      ))}
                    </div>
                  )}
                  <div className="question-answer">
                    <strong>答案：</strong>{q.answer}
                  </div>
                  <div className="question-explanation">
                    <strong>解析：</strong>{q.explanation}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="step-actions">
            <button onClick={() => setStep('select')} className="btn-secondary">
              🔄 重新生成
            </button>
            <button onClick={() => {/* TODO: 导出功能 */}} className="btn-primary">
              📥 导出题目
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// ==============================================================================
// 3. 试卷生成界面
// ==============================================================================
const PaperGeneratorTab: React.FC = () => {
  const [questions, setQuestions] = useState<any[]>([]);
  const [selectedQuestions, setSelectedQuestions] = useState<number[]>([]);
  const [paperTitle, setPaperTitle] = useState('');
  const [totalScore, setTotalScore] = useState(100);
  const [duration, setDuration] = useState(90);
  const [loading, setLoading] = useState(false);
  const [papers, setPapers] = useState<any[]>([]);

  useEffect(() => {
    loadQuestions();
    loadPapers();
  }, []);

  const loadQuestions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/ai-learning/my_questions`, {
        headers: getAuthHeaders(),
        params: { page: 1, page_size: 50 }
      });
      setQuestions(response.data.questions);
    } catch (error) {
      alert('加载题目失败');
    }
  };

  const loadPapers = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/papers/`, {
        headers: getAuthHeaders()
      });
      setPapers(response.data.papers);
    } catch (error) {
      console.error('加载试卷失败', error);
    }
  };

  const generatePaper = async () => {
    if (!paperTitle.trim()) {
      alert('请输入试卷标题');
      return;
    }
    if (selectedQuestions.length === 0) {
      alert('请至少选择一道题目');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/papers/`,
        {
          title: paperTitle,
          question_ids: selectedQuestions,
          total_score: totalScore,
          duration_minutes: duration,
          subject: '数学'
        },
        { headers: getAuthHeaders() }
      );
      alert('✅ 试卷生成成功！');
      loadPapers();
      // 重置
      setSelectedQuestions([]);
      setPaperTitle('');
    } catch (error: any) {
      alert('生成失败：' + (error.response?.data?.detail || '网络错误'));
    } finally {
      setLoading(false);
    }
  };

  const downloadPaper = (paperId: number, version: 'student' | 'teacher') => {
    const url = `${API_BASE_URL}/papers/${paperId}/download/${version}`;
    window.open(url + '?token=' + getToken(), '_blank');
  };

  const toggleQuestionSelection = (id: number) => {
    setSelectedQuestions(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  return (
    <div className="paper-generator-tab">
      <h2>📄 试卷生成</h2>

      <div className="paper-sections">
        {/* 左侧：选题 */}
        <div className="section">
          <h3>1. 选择题目（可多选）</h3>
          {questions.length === 0 ? (
            <div className="empty-state">
              <p>还没有生成题目</p>
              <p>请先去"智能出题"生成题目</p>
            </div>
          ) : (
            <div className="selectable-list">
              {questions.map((q) => {
                const content = JSON.parse(q.content);
                return (
                  <div 
                    key={q.id}
                    className={`selectable-item ${selectedQuestions.includes(q.id) ? 'selected' : ''}`}
                    onClick={() => toggleQuestionSelection(q.id)}
                  >
                    <input 
                      type="checkbox" 
                      checked={selectedQuestions.includes(q.id)}
                      readOnly
                    />
                    <div>
                      <div className="item-title">
                        [{q.question_type}] {content.stem.substring(0, 40)}...
                      </div>
                      <div className="item-meta">难度: {q.difficulty}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* 右侧：设置 */}
        <div className="section">
          <h3>2. 设置试卷信息</h3>
          <div className="form-group">
            <label>试卷标题：</label>
            <input 
              type="text"
              value={paperTitle}
              onChange={(e) => setPaperTitle(e.target.value)}
              placeholder="例如：期中考试（数学）"
            />
          </div>
          <div className="form-group">
            <label>总分：</label>
            <input 
              type="number"
              value={totalScore}
              onChange={(e) => setTotalScore(parseInt(e.target.value) || 100)}
            />
          </div>
          <div className="form-group">
            <label>时长（分钟）：</label>
            <input 
              type="number"
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value) || 90)}
            />
          </div>
          <button 
            onClick={generatePaper}
            disabled={loading || selectedQuestions.length === 0}
            className="btn-primary btn-large"
          >
            {loading ? '正在生成...' : `📄 生成试卷 (已选${selectedQuestions.length}题)`}
          </button>
        </div>
      </div>

      {/* 已生成的试卷列表 */}
      <div className="section">
        <h3>3. 我的试卷</h3>
        {papers.length === 0 ? (
          <div className="empty-state">还没有生成试卷</div>
        ) : (
          <div className="papers-list">
            {papers.map((paper) => (
              <div key={paper.id} className="paper-card">
                <div className="paper-header">
                  <h4>{paper.title}</h4>
                  <span className="paper-score">{paper.total_score}分</span>
                </div>
                <div className="paper-info">
                  题目数: {paper.question_count} | 
                  时长: {paper.duration_minutes}分钟 | 
                  创建时间: {new Date(paper.created_at).toLocaleString()}
                </div>
                <div className="paper-actions">
                  <button 
                    onClick={() => downloadPaper(paper.id, 'student')}
                    className="btn-secondary"
                  >
                    📥 下载学生版
                  </button>
                  <button 
                    onClick={() => downloadPaper(paper.id, 'teacher')}
                    className="btn-primary"
                  >
                    📥 下载教师版
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ==============================================================================
// 主界面
// ==============================================================================
const PersonalLearning: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'mistakes' | 'generator' | 'papers'>('mistakes');

  return (
    <div className="personal-learning">
      <div className="tab-nav">
        <button 
          className={activeTab === 'mistakes' ? 'active' : ''}
          onClick={() => setActiveTab('mistakes')}
        >
          📚 错题本
        </button>
        <button 
          className={activeTab === 'generator' ? 'active' : ''}
          onClick={() => setActiveTab('generator')}
        >
          🎯 智能出题
        </button>
        <button 
          className={activeTab === 'papers' ? 'active' : ''}
          onClick={() => setActiveTab('papers')}
        >
          📄 试卷生成
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'mistakes' && <MistakeBookTab />}
        {activeTab === 'generator' && <QuestionGeneratorTab />}
        {activeTab === 'papers' && <PaperGeneratorTab />}
      </div>
    </div>
  );
};

export default PersonalLearning;

