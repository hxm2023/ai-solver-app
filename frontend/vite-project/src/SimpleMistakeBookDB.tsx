// ==============================================================================
// SimpleMistakeBookDB.tsx - 数据库版错题本完整界面（需要登录）
// ==============================================================================

import React, { useState, useEffect } from 'react';
import { AuthModal } from './components/AuthModal';
import TextItem from './components/TextItem';
import { 
  isAuthenticated, 
  getUserInfo, 
  clearAuth,
  authenticatedFetch 
} from './utils/api';
import './SimpleMistakeBookDB.css';

interface SimpleMistakeBookDBProps {
  hideAuth?: boolean;  // 是否隐藏认证界面（当从AppDB调用时）
}

interface Mistake {
  id: string;
  image_base64: string;
  question_text: string;
  wrong_answer: string;
  ai_analysis: string;
  subject: string;
  grade: string;
  knowledge_points: string[];
  created_at: string;
  reviewed_count: number;
}

interface Question {
  id: string;
  content: string;
  answer: string;
  explanation: string;
  knowledge_points: string[];
  difficulty: string;
  created_at: string;
  subject?: string;
  grade?: string;
}

// 【新增】工具函数：标准化 knowledge_points 字段
// 后端可能返回字符串、JSON字符串或数组，统一转换为数组
function normalizeKnowledgePoints(kp: any): string[] {
  // 如果已经是数组，直接返回
  if (Array.isArray(kp)) {
    return kp;
  }
  
  // 如果是字符串
  if (typeof kp === 'string') {
    // 尝试解析为 JSON 数组
    try {
      const parsed = JSON.parse(kp);
      if (Array.isArray(parsed)) {
        return parsed;
      }
    } catch {
      // 如果不是 JSON，按逗号分隔
      return kp.split(',').map(s => s.trim()).filter(s => s.length > 0);
    }
  }
  
  // 其他情况返回空数组
  return [];
}

const SimpleMistakeBookDB: React.FC<SimpleMistakeBookDBProps> = ({ hideAuth = false }) => {
  // 认证状态
  const [user, setUser] = useState<any>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  
  // 数据状态
  const [activeTab, setActiveTab] = useState<'mistakes' | 'questions' | 'generate'>('mistakes');
  const [mistakes, setMistakes] = useState<Mistake[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [selectedMistakes, setSelectedMistakes] = useState<Set<string>>(new Set());
  const [selectedKnowledgePoints, setSelectedKnowledgePoints] = useState<Set<string>>(new Set());
  const [selectedQuestions, setSelectedQuestions] = useState<Set<string>>(new Set());
  const [allKnowledgePoints, setAllKnowledgePoints] = useState<string[]>([]);
  
  // 出题配置（V25.2新增学科和年级）
  const [paperConfig, setPaperConfig] = useState({
    count: 5,
    difficulty: '中等',
    questionType: '选择题',
    allowWebSearch: false,
    subject: '数学',  // V25.2新增
    grade: '高一'     // V25.2新增
  });
  
  // 加载状态
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // 筛选条件
  const [filterSubject, setFilterSubject] = useState<string>('');
  const [filterGrade, setFilterGrade] = useState<string>('');

  // 【修复】参考本地版本的简单有效方法
  useEffect(() => {
    if (mistakes.length > 0 || questions.length > 0 || activeTab) {
      // 延迟200ms后渲染公式（给DOM更新留时间）
      setTimeout(() => {
        const contentDivs = document.querySelectorAll('.math-content, .message-content, .mistake-section, .question-section');
        if (contentDivs.length > 0 && window.MathJax?.typesetPromise) {
          window.MathJax.typesetPromise(Array.from(contentDivs))
            .then(() => console.log('✅ [MathJax] 错题本公式渲染完成'))
            .catch((err: any) => console.error('❌ [MathJax] 渲染错误:', err));
        }
      }, 200);
    }
  }, [mistakes, questions, activeTab]);

  // 组件挂载时检查登录状态
  useEffect(() => {
    if (isAuthenticated()) {
      const userInfo = getUserInfo();
      setUser(userInfo);
      loadData();
    } else if (!hideAuth) {
      setShowAuthModal(true);
    }

    // 监听未授权事件
    const handleUnauthorized = () => {
      if (!hideAuth) {
        setUser(null);
        setShowAuthModal(true);
      }
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, [hideAuth]);

  // 加载数据
  const loadData = async () => {
    setLoading(true);
    setError('');

    try {
      // 构建查询参数（V25.2使用新API）
      const mistakesParams = new URLSearchParams();
      mistakesParams.append('limit', '100');
      // V25.2: 使用subject_name参数而不是subject
      if (filterSubject) mistakesParams.append('subject_name', filterSubject);
      if (filterGrade) mistakesParams.append('grade', filterGrade);
      
      // 并行加载错题和题目
      // V25.2: 优先使用新API，如果失败则降级到旧API
      const [mistakesRes, questionsRes] = await Promise.all([
        authenticatedFetch(`/api/v2/mistakes?${mistakesParams.toString()}`).catch(() => 
          authenticatedFetch(`/mistakes/?${mistakesParams.toString()}`)
        ),
        authenticatedFetch('/questions/?limit=100')
      ]);

      const mistakesData = await mistakesRes.json();
      const questionsData = await questionsRes.json();

      // V25.2 API返回格式：{success, mistakes, total}
      // 旧API返回格式：{items}
      const mistakesList = mistakesData.mistakes || mistakesData.items || [];
      
      // 【调试】打印前3条错题数据
      console.log('\n[错题本数据调试] 接收到错题数量:', mistakesList.length);
      if (mistakesList.length > 0) {
        console.log('[错题本数据调试] 第1条错题原始数据:', mistakesList[0]);
        console.log('  - question_text:', mistakesList[0]?.question_text);
        console.log('  - wrong_answer:', mistakesList[0]?.wrong_answer);
        console.log('  - ai_analysis:', mistakesList[0]?.ai_analysis);
        console.log('  - knowledge_points:', mistakesList[0]?.knowledge_points);
      }
      
      // 【修复】标准化 knowledge_points 字段，确保是数组
      const normalizedMistakes = mistakesList.map((m: any) => ({
        ...m,
        knowledge_points: normalizeKnowledgePoints(m.knowledge_points)
      }));
      
      const normalizedQuestions = (questionsData.items || []).map((q: any) => ({
        ...q,
        knowledge_points: normalizeKnowledgePoints(q.knowledge_points)
      }));
      
      setMistakes(normalizedMistakes);
      setQuestions(normalizedQuestions);
      
      // 提取所有唯一的知识点（使用标准化后的数据）
      const knowledgePointsSet = new Set<string>();
      normalizedMistakes.forEach((mistake: Mistake) => {
        if (mistake.knowledge_points && Array.isArray(mistake.knowledge_points)) {
          mistake.knowledge_points.forEach(kp => knowledgePointsSet.add(kp));
        }
      });
      setAllKnowledgePoints(Array.from(knowledgePointsSet).sort());
      
    } catch (err: any) {
      setError('加载数据失败: ' + (err.message || '未知错误'));
      console.error('加载数据错误:', err);
    } finally {
      setLoading(false);
    }
  };

  // 登录成功回调
  const handleLoginSuccess = (userInfo: any) => {
    setUser(userInfo);
    setShowAuthModal(false);
    loadData();
  };

  // 退出登录
  const handleLogout = () => {
    clearAuth();
    setUser(null);
    setMistakes([]);
    setQuestions([]);
    setShowAuthModal(true);
  };

  // 删除错题
  const handleDeleteMistake = async (id: string) => {
    if (!confirm('确定要删除这道错题吗？')) return;

    try {
      const response = await authenticatedFetch(`/mistakes/${id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('删除失败');
      
      setMistakes(mistakes.filter(m => m.id !== id));
      alert('删除成功！');
    } catch (err: any) {
      alert('删除失败: ' + (err.message || '未知错误'));
    }
  };

  // 删除题目
  const handleDeleteQuestion = async (id: string) => {
    if (!confirm('确定要删除这道题目吗？')) return;

    try {
      const response = await authenticatedFetch(`/questions/${id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('删除失败');
      
      setQuestions(questions.filter(q => q.id !== id));
      alert('删除成功！');
    } catch (err: any) {
      alert('删除失败: ' + (err.message || '未知错误'));
    }
  };

  // 生成试卷
  const generatePaper = async () => {
    // 收集需要生成的错题ID
    let targetMistakeIds: string[] = [];
    
    if (selectedKnowledgePoints.size > 0) {
      // 基于知识点筛选错题
      const filteredMistakes = mistakes.filter(m => 
        m.knowledge_points && m.knowledge_points.some(kp => 
          selectedKnowledgePoints.has(kp)
        )
      );
      targetMistakeIds = filteredMistakes.map(m => m.id);
    } else if (selectedMistakes.size > 0) {
      // 直接使用选中的错题
      targetMistakeIds = Array.from(selectedMistakes);
    } else {
      alert('请先选择知识点或错题');
      return;
    }

    if (targetMistakeIds.length === 0) {
      alert('没有找到匹配的错题');
      return;
    }

    setLoading(true);
    try {
      // V25.2: 尝试使用新API，如果失败则降级到旧API
      let response;
      try {
        // 尝试V25.2 API（支持学科和年级）
        response = await authenticatedFetch('/api/v2/papers/generate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            subject: paperConfig.subject,
            grade: paperConfig.grade,
            paper_title: `${paperConfig.subject}_${paperConfig.grade}_练习卷`,
            question_types: [paperConfig.questionType],
            difficulty: paperConfig.difficulty,
            total_score: 100,
            duration_minutes: 90,
            knowledge_points: Array.from(selectedKnowledgePoints)
          })
        });
      } catch (e) {
        // 降级到旧API
        console.log('V25.2 API不可用，使用旧API');
        response = await authenticatedFetch('/questions/generate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            mistake_ids: targetMistakeIds,
            count: paperConfig.count,
            difficulty: paperConfig.difficulty,
            allow_web_search: paperConfig.allowWebSearch
          })
        });
      }
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '生成失败');
      }
      
      const data = await response.json();
      
      // V25.2 API返回格式不同
      const questionCount = data.question_ids?.length || data.questions?.length || 0;
      const subject = data.subject || paperConfig.subject;
      const grade = data.grade || paperConfig.grade;
      
      alert(`✅ 成功生成试卷！\n学科：${subject}\n年级：${grade}\n题目数量：${questionCount}道`);
      setSelectedMistakes(new Set());
      setSelectedKnowledgePoints(new Set());
      await loadData();
      setActiveTab('questions');
    } catch (error: any) {
      console.error('生成题目失败:', error);
      alert('生成题目失败: ' + (error.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };

  // 导出为PDF
  const exportPDF = async (questionIds: string[]) => {
    if (questionIds.length === 0) {
      alert('请先选择要导出的题目');
      return;
    }

    try {
      const response = await authenticatedFetch('/export/pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question_ids: questionIds,
          title: '练习题集',
          include_answers: true
        })
      });
      
      if (!response.ok) throw new Error('导出失败');
      
      // 接收二进制数据
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `练习题集_${new Date().toISOString().slice(0,10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      alert('PDF导出成功！');
    } catch (error: any) {
      console.error('导出失败:', error);
      alert('导出失败: ' + (error.message || '未知错误'));
    }
  };

  // 导出选中的题目
  const exportSelectedQuestions = () => {
    if (selectedQuestions.size === 0) {
      alert('请先选择要导出的题目');
      return;
    }
    exportPDF(Array.from(selectedQuestions));
  };

  // 渲染用户信息栏
  const renderUserInfo = () => {
    if (!user) return null;

    return (
      <div className="user-info-bar">
        <div className="user-info-left">
          <span className="user-avatar">👤</span>
          <span className="user-nickname">{user.nickname || user.account}</span>
          <span className="user-id">ID: {user.user_id?.slice(0, 8)}</span>
        </div>
        <button className="logout-btn" onClick={handleLogout}>
          退出登录
        </button>
      </div>
    );
  };

  // 渲染统计卡片
  const renderStats = () => {
    return (
      <div className="stats-container">
        <div className="stat-card">
          <div className="stat-value">{mistakes.length}</div>
          <div className="stat-label">错题总数</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{questions.length}</div>
          <div className="stat-label">练习题数</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{allKnowledgePoints.length}</div>
          <div className="stat-label">知识点数</div>
        </div>
      </div>
    );
  };

  // 渲染错题列表
  const renderMistakes = () => {
    if (loading) {
      return <div className="loading-message">加载中...</div>;
    }

    if (error) {
      return (
        <div className="error-message">
          ⚠️ {error}
          <button onClick={loadData} style={{ marginLeft: '10px' }}>
            重新加载
          </button>
        </div>
      );
    }

    if (mistakes.length === 0) {
      return (
        <div className="empty-message">
          📝 还没有错题，使用"AI批改作业"功能开始记录吧！
        </div>
      );
    }

    return (
      <>
        {/* V25.2新增：学科和年级筛选器 */}
        <div style={{
          marginBottom: '20px',
          padding: '20px',
          background: 'white',
          borderRadius: '10px',
          border: '2px solid #f0f0f0',
          display: 'flex',
          gap: '15px',
          alignItems: 'flex-end',
          flexWrap: 'wrap'
        }}>
          <div style={{ flex: '1', minWidth: '200px' }}>
            <label style={{ 
              display: 'block', 
              marginBottom: '8px', 
              fontSize: '14px', 
              fontWeight: 'bold',
              color: '#333'
            }}>
              📚 学科筛选
            </label>
            <select
              value={filterSubject}
              onChange={(e) => {
                setFilterSubject(e.target.value);
                // 筛选条件改变后重新加载数据
                setTimeout(() => loadData(), 0);
              }}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '14px',
                background: 'white',
                cursor: 'pointer'
              }}
            >
              <option value="">全部学科</option>
              <option value="数学">数学</option>
              <option value="物理">物理</option>
              <option value="化学">化学</option>
              <option value="生物">生物</option>
              <option value="语文">语文</option>
              <option value="英语">英语</option>
              <option value="历史">历史</option>
              <option value="地理">地理</option>
              <option value="政治">政治</option>
            </select>
          </div>

          <div style={{ flex: '1', minWidth: '200px' }}>
            <label style={{ 
              display: 'block', 
              marginBottom: '8px', 
              fontSize: '14px', 
              fontWeight: 'bold',
              color: '#333'
            }}>
              🎓 年级筛选
            </label>
            <select
              value={filterGrade}
              onChange={(e) => {
                setFilterGrade(e.target.value);
                setTimeout(() => loadData(), 0);
              }}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ddd',
                borderRadius: '6px',
                fontSize: '14px',
                background: 'white',
                cursor: 'pointer'
              }}
            >
              <option value="">全部年级</option>
              <option value="初一">初一</option>
              <option value="初二">初二</option>
              <option value="初三">初三</option>
              <option value="高一">高一</option>
              <option value="高二">高二</option>
              <option value="高三">高三</option>
            </select>
          </div>

          <button
            onClick={() => {
              setFilterSubject('');
              setFilterGrade('');
              setTimeout(() => loadData(), 0);
            }}
            style={{
              padding: '10px 20px',
              background: '#f0f0f0',
              border: '1px solid #ddd',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 'bold',
              color: '#666',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = '#e0e0e0';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = '#f0f0f0';
            }}
          >
            🔄 清除筛选
          </button>

          {(filterSubject || filterGrade) && (
            <div style={{
              flex: '1 1 100%',
              padding: '10px',
              background: '#e3f2fd',
              borderRadius: '6px',
              fontSize: '14px',
              color: '#1976d2'
            }}>
              ✓ 已筛选：
              {filterSubject && <span style={{ marginLeft: '10px', fontWeight: 'bold' }}>{filterSubject}</span>}
              {filterGrade && <span style={{ marginLeft: '10px', fontWeight: 'bold' }}>{filterGrade}</span>}
              {' '}（共 {mistakes.length} 道错题）
            </div>
          )}
        </div>

        <div className="mistakes-list">
          {mistakes.map((mistake) => (
            <div key={mistake.id} className="mistake-card">
            <div className="mistake-header">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={selectedMistakes.has(mistake.id)}
                  onChange={(e) => {
                    const newSet = new Set(selectedMistakes);
                    if (e.target.checked) {
                      newSet.add(mistake.id);
                    } else {
                      newSet.delete(mistake.id);
                    }
                    setSelectedMistakes(newSet);
                  }}
                  style={{ width: '16px', height: '16px' }}
                />
                <span className="mistake-subject">{mistake.subject}</span>
              </label>
              <span className="mistake-grade">{mistake.grade}</span>
              <span className="mistake-date">
                {new Date(mistake.created_at).toLocaleDateString()}
              </span>
              <button 
                className="delete-btn"
                onClick={() => handleDeleteMistake(mistake.id)}
              >
                🗑️ 删除
              </button>
            </div>
            
            {mistake.image_base64 && (
              <img 
                src={`data:image/png;base64,${mistake.image_base64}`}
                alt="错题图片"
                className="mistake-image"
              />
            )}
            
            <div className="mistake-content">
              <div className="mistake-section">
                <h4>题目：</h4>
                <TextItem content={mistake.question_text} />
              </div>
              
              <div className="mistake-section">
                <h4>我的答案：</h4>
                <TextItem content={mistake.wrong_answer} />
              </div>
              
              <div className="mistake-section">
                <h4>AI分析：</h4>
                <TextItem content={mistake.ai_analysis} />
              </div>
              
              {Array.isArray(mistake.knowledge_points) && mistake.knowledge_points.length > 0 && (
                <div className="knowledge-points">
                  <strong>知识点：</strong>
                  {mistake.knowledge_points.map((kp, idx) => (
                    <span key={idx} className="knowledge-point-tag">
                      {kp}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        </div>
      </>
    );
  };

  // 渲染题目列表
  const renderQuestions = () => {
    if (loading) {
      return <div className="loading-message">加载中...</div>;
    }

    if (error) {
      return (
        <div className="error-message">
          ⚠️ {error}
          <button onClick={loadData} style={{ marginLeft: '10px' }}>
            重新加载
          </button>
        </div>
      );
    }

    if (questions.length === 0) {
      return (
        <div className="empty-message">
          📚 还没有练习题，前往"智能出题"标签页生成题目吧！
        </div>
      );
    }

    return (
      <>
        {/* 导出按钮 */}
        <div style={{ marginBottom: '20px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            onClick={exportSelectedQuestions}
            disabled={selectedQuestions.size === 0}
            style={{
              padding: '10px 20px',
              background: selectedQuestions.size > 0 ? '#4CAF50' : '#ccc',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: selectedQuestions.size > 0 ? 'pointer' : 'not-allowed',
              fontSize: '14px',
              fontWeight: 'bold'
            }}
          >
            📄 导出选中题目为PDF ({selectedQuestions.size})
          </button>
          
          <button
            onClick={() => exportPDF(questions.map(q => q.id))}
            style={{
              padding: '10px 20px',
              background: '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 'bold'
            }}
          >
            📄 导出全部题目为PDF ({questions.length})
          </button>
        </div>

        {/* 题目列表 */}
        <div className="questions-list">
          {questions.map((question) => (
            <div key={question.id} className="question-card">
              <div className="question-header">
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={selectedQuestions.has(question.id)}
                    onChange={(e) => {
                      const newSet = new Set(selectedQuestions);
                      if (e.target.checked) {
                        newSet.add(question.id);
                      } else {
                        newSet.delete(question.id);
                      }
                      setSelectedQuestions(newSet);
                    }}
                    style={{ width: '16px', height: '16px' }}
                  />
                  <span className="question-difficulty">{question.difficulty}</span>
                </label>
                {question.subject && (
                  <span className="question-subject">{question.subject}</span>
                )}
                {question.grade && (
                  <span className="question-grade">{question.grade}</span>
                )}
                <span className="question-date">
                  {new Date(question.created_at).toLocaleDateString()}
                </span>
                <button 
                  className="delete-btn"
                  onClick={() => handleDeleteQuestion(question.id)}
                >
                  🗑️ 删除
                </button>
              </div>
              
              <div className="question-content">
                <div className="question-section">
                  <h4>题目：</h4>
                  <TextItem content={question.content} />
                </div>
                
                <details className="question-answer-details">
                  <summary>查看答案</summary>
                  <div className="question-section">
                    <h4>答案：</h4>
                    <TextItem content={question.answer} />
                  </div>
                </details>
                
                <details className="question-explanation-details">
                  <summary>查看解析</summary>
                  <div className="question-section">
                    <h4>解析：</h4>
                    <TextItem content={question.explanation} />
                  </div>
                </details>
                
                {Array.isArray(question.knowledge_points) && question.knowledge_points.length > 0 && (
                  <div className="knowledge-points">
                    <strong>知识点：</strong>
                    {question.knowledge_points.map((kp, idx) => (
                      <span key={idx} className="knowledge-point-tag">
                        {kp}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </>
    );
  };

  // 渲染智能出题界面
  const renderGenerate = () => {
    if (mistakes.length === 0) {
      return (
        <div className="empty-message">
          📝 还没有错题，无法生成练习题。<br/>
          请先使用"AI批改作业"功能添加错题！
        </div>
      );
    }

    return (
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* 选择方式说明 */}
        <div style={{
          marginBottom: '30px',
          padding: '20px',
          background: '#e3f2fd',
          borderRadius: '10px',
          borderLeft: '4px solid #2196F3'
        }}>
          <h3 style={{ marginBottom: '15px', color: '#1976d2' }}>📋 选择生成方式</h3>
          <p style={{ fontSize: '14px', color: '#555', lineHeight: '1.8' }}>
            您可以选择：<br/>
            1️⃣ <strong>按知识点选择</strong>：系统会找到所有相关错题，适合针对性训练<br/>
            2️⃣ <strong>直接选择错题</strong>：基于特定错题生成练习，适合巩固具体题目
          </p>
        </div>

        {/* 按知识点选择 */}
        <div style={{
          marginBottom: '30px',
          padding: '20px',
          background: 'white',
          borderRadius: '10px',
          border: '2px solid #ddd'
        }}>
          <h3 style={{ marginBottom: '15px', color: '#333' }}>
            🎯 按知识点选择 ({selectedKnowledgePoints.size} 个已选)
          </h3>
          
          {allKnowledgePoints.length === 0 ? (
            <p style={{ color: '#999', fontSize: '14px' }}>暂无知识点</p>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
              gap: '10px'
            }}>
              {allKnowledgePoints.map((kp) => (
                <label
                  key={kp}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '10px',
                    background: selectedKnowledgePoints.has(kp) ? '#e8f5e9' : '#f5f5f5',
                    border: selectedKnowledgePoints.has(kp) ? '2px solid #4CAF50' : '1px solid #ddd',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedKnowledgePoints.has(kp)}
                    onChange={(e) => {
                      const newSet = new Set(selectedKnowledgePoints);
                      if (e.target.checked) {
                        newSet.add(kp);
                      } else {
                        newSet.delete(kp);
                      }
                      setSelectedKnowledgePoints(newSet);
                    }}
                    style={{ width: '16px', height: '16px' }}
                  />
                  <span style={{ fontSize: '13px', color: '#333' }}>{kp}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* 或者直接选择错题 */}
        <div style={{
          marginBottom: '30px',
          padding: '20px',
          background: 'white',
          borderRadius: '10px',
          border: '2px solid #ddd'
        }}>
          <h3 style={{ marginBottom: '15px', color: '#333' }}>
            📝 或者直接选择错题 ({selectedMistakes.size} 道已选)
          </h3>
          <p style={{ fontSize: '13px', color: '#666', marginBottom: '15px' }}>
            前往"我的错题"标签页勾选需要的错题
          </p>
          {selectedMistakes.size > 0 && (
            <div style={{
              padding: '12px',
              background: '#e8f5e9',
              borderRadius: '6px',
              fontSize: '14px',
              color: '#2e7d32'
            }}>
              ✓ 已选择 {selectedMistakes.size} 道错题
            </div>
          )}
        </div>

        {/* 出题配置 */}
        <div style={{
          marginBottom: '30px',
          padding: '20px',
          background: 'white',
          borderRadius: '10px',
          border: '2px solid #ddd'
        }}>
          <h3 style={{ marginBottom: '20px', color: '#333' }}>⚙️ 出题配置</h3>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '20px'
          }}>
            {/* V25.2新增：学科选择 */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 'bold' }}>
                📚 学科
              </label>
              <select
                value={paperConfig.subject}
                onChange={(e) => setPaperConfig({...paperConfig, subject: e.target.value})}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px',
                  background: 'white',
                  cursor: 'pointer'
                }}
              >
                <option value="数学">数学</option>
                <option value="物理">物理</option>
                <option value="化学">化学</option>
                <option value="生物">生物</option>
                <option value="语文">语文</option>
                <option value="英语">英语</option>
                <option value="历史">历史</option>
                <option value="地理">地理</option>
                <option value="政治">政治</option>
              </select>
            </div>

            {/* V25.2新增：年级选择 */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 'bold' }}>
                🎓 年级
              </label>
              <select
                value={paperConfig.grade}
                onChange={(e) => setPaperConfig({...paperConfig, grade: e.target.value})}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px',
                  background: 'white',
                  cursor: 'pointer'
                }}
              >
                <option value="初一">初一</option>
                <option value="初二">初二</option>
                <option value="初三">初三</option>
                <option value="高一">高一</option>
                <option value="高二">高二</option>
                <option value="高三">高三</option>
              </select>
            </div>

            {/* 题目数量 */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 'bold' }}>
                题目数量
              </label>
              <input
                type="number"
                min="1"
                max="20"
                value={paperConfig.count}
                onChange={(e) => setPaperConfig({...paperConfig, count: parseInt(e.target.value) || 5})}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
            </div>

            {/* 难度 */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 'bold' }}>
                难度
              </label>
              <select
                value={paperConfig.difficulty}
                onChange={(e) => setPaperConfig({...paperConfig, difficulty: e.target.value})}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              >
                <option value="简单">简单</option>
                <option value="中等">中等</option>
                <option value="困难">困难</option>
              </select>
            </div>

            {/* 题型 */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 'bold' }}>
                题型
              </label>
              <select
                value={paperConfig.questionType}
                onChange={(e) => setPaperConfig({...paperConfig, questionType: e.target.value})}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              >
                <option value="选择题">选择题</option>
                <option value="填空题">填空题</option>
                <option value="解答题">解答题</option>
                <option value="混合题型">混合题型</option>
              </select>
            </div>
          </div>

          {/* 网络辅助出题选项 */}
          <div style={{
            marginTop: '20px',
            padding: '15px',
            background: 'white',
            borderRadius: '8px',
            border: paperConfig.allowWebSearch ? '2px solid #4CAF50' : '1px solid #ddd'
          }}>
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              cursor: 'pointer',
              fontSize: '14px'
            }}>
              <input
                type="checkbox"
                checked={paperConfig.allowWebSearch}
                onChange={(e) => setPaperConfig({...paperConfig, allowWebSearch: e.target.checked})}
                style={{
                  width: '18px',
                  height: '18px',
                  cursor: 'pointer'
                }}
              />
              <span style={{ fontWeight: 'bold', color: paperConfig.allowWebSearch ? '#4CAF50' : '#333' }}>
                🌐 允许网络搜索辅助出题
              </span>
            </label>
            <p style={{
              fontSize: '12px',
              color: '#666',
              margin: '8px 0 0 28px',
              lineHeight: '1.6'
            }}>
              {paperConfig.allowWebSearch ? (
                <span style={{ color: '#4CAF50' }}>
                  ✓ AI将搜索相关题库网站作为参考，生成更真实、更高质量的题目
                </span>
              ) : (
                '开启后，AI会搜索网络上的相关题目作为参考，提升题目质量和真实性'
              )}
            </p>
          </div>
        </div>

        {/* 生成按钮 */}
        <div style={{
          textAlign: 'center',
          padding: '30px',
          background: 'white',
          border: '2px dashed #5C6AC4',
          borderRadius: '10px'
        }}>
          <button
            onClick={generatePaper}
            disabled={loading || (selectedMistakes.size === 0 && selectedKnowledgePoints.size === 0)}
            style={{
              padding: '18px 50px',
              fontSize: '18px',
              background: (selectedMistakes.size > 0 || selectedKnowledgePoints.size > 0) ? 
                'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#ccc',
              color: 'white',
              border: 'none',
              borderRadius: '10px',
              cursor: (selectedMistakes.size > 0 || selectedKnowledgePoints.size > 0) ? 'pointer' : 'not-allowed',
              fontWeight: 'bold',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
            }}
          >
            {loading ? '⏳ 生成中...' : '🚀 生成专属试卷'}
          </button>
          
          {(selectedMistakes.size > 0 || selectedKnowledgePoints.size > 0) && (
            <p style={{ marginTop: '15px', color: '#666', fontSize: '14px' }}>
              💡 将生成 {paperConfig.count} 道{paperConfig.difficulty}难度的{paperConfig.questionType}
              <br/>
              📚 学科：{paperConfig.subject}  🎓 年级：{paperConfig.grade}
              <br/>
              生成后可在"练习题库"标签页查看和导出PDF
            </p>
          )}
        </div>

        {/* 使用说明 */}
        <div style={{
          marginTop: '30px',
          padding: '20px',
          background: '#fff3e0',
          borderRadius: '10px',
          borderLeft: '4px solid #ff9800'
        }}>
          <h4 style={{ marginBottom: '10px', color: '#f57c00' }}>💡 使用提示</h4>
          <ul style={{ fontSize: '13px', color: '#666', lineHeight: '1.8', paddingLeft: '20px' }}>
            <li>选择<strong>知识点</strong>：系统会找到所有包含该知识点的错题，适合针对性训练</li>
            <li>选择<strong>错题</strong>：直接基于选中的错题生成练习，适合巩固具体题目</li>
            <li>生成后的题目会显示在"练习题库"标签页，包含详细解析</li>
            <li>可以勾选多道题目，一键导出为PDF文件打印使用</li>
            <li>开启<strong>网络辅助</strong>，AI会搜索真实题库，生成更高质量的题目</li>
          </ul>
        </div>
      </div>
    );
  };

  return (
    <div className="simple-mistake-book">
      {/* 认证模态框（仅在独立使用时显示） */}
      {!hideAuth && (
        <AuthModal 
          isOpen={showAuthModal}
          onClose={() => {}}  // 必须登录，不允许关闭
          onLoginSuccess={handleLoginSuccess}
        />
      )}

      {/* 主界面（登录后显示，或从AppDB调用时直接显示） */}
      {(user || hideAuth) && (
        <>
          {/* 标题栏和用户信息（仅在独立使用时显示） */}
          {!hideAuth && (
            <>
              {/* 标题栏 */}
              <div className="app-header">
                <h1>🗄️ 沐梧AI - 数据库版本 V25.1</h1>
                <p className="app-subtitle">
                  ✨ MySQL存储 • JWT认证 • 多用户支持
                </p>
              </div>

              {/* 用户信息栏 */}
              {renderUserInfo()}
            </>
          )}

          {/* 统计卡片 */}
          {renderStats()}

          {/* 标签页 */}
          <div className="tabs-container">
            <button
              className={`tab-button ${activeTab === 'mistakes' ? 'active' : ''}`}
              onClick={() => setActiveTab('mistakes')}
            >
              📝 我的错题 ({mistakes.length})
            </button>
            <button
              className={`tab-button ${activeTab === 'questions' ? 'active' : ''}`}
              onClick={() => setActiveTab('questions')}
            >
              📚 练习题库 ({questions.length})
            </button>
            <button
              className={`tab-button ${activeTab === 'generate' ? 'active' : ''}`}
              onClick={() => setActiveTab('generate')}
            >
              🎯 智能出题
            </button>
          </div>

          {/* 内容区域 */}
          <div className="tab-content">
            {activeTab === 'mistakes' && renderMistakes()}
            {activeTab === 'questions' && renderQuestions()}
            {activeTab === 'generate' && renderGenerate()}
          </div>
        </>
      )}
    </div>
  );
};

export default SimpleMistakeBookDB;
