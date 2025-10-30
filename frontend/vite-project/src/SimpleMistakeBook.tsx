// ==============================================================================
// SimpleMistakeBook.tsx - 简化版错题本界面（无需登录）
// ==============================================================================

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { marked } from 'marked';
import QuestionItem from './components/QuestionItem';

const API_BASE_URL = 'http://127.0.0.1:8000';

// 配置marked以保护LaTeX公式
marked.setOptions({
  breaks: true,
  gfm: true,
  pedantic: false,
  sanitize: false,
  smartLists: true,
  smartypants: false, // 关键：不要转换引号和破折号
});

// 声明MathJax类型
declare global {
  interface Window {
    MathJax: any;
  }
}

interface Mistake {
  id: string;
  image_base64: string;
  question_text: string;
  wrong_answer: string;
  ai_analysis: string;
  subject: string;
  grade: string;  // 【V25.0新增】年级
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
}

const SimpleMistakeBook: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'mistakes' | 'questions' | 'generate' | 'papergen'>('mistakes');
  const [mistakes, setMistakes] = useState<Mistake[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [selectedMistakes, setSelectedMistakes] = useState<Set<string>>(new Set());
  const [selectedKnowledgePoints, setSelectedKnowledgePoints] = useState<Set<string>>(new Set());
  const [selectedQuestions, setSelectedQuestions] = useState<Set<string>>(new Set());
  const [paperConfig, setPaperConfig] = useState({
    count: 5,
    difficulty: '中等',
    questionType: '选择题',
    allowWebSearch: false  // 【V25.0新增】网络辅助出题
  });
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [allKnowledgePoints, setAllKnowledgePoints] = useState<string[]>([]);
  // 【V25.0新增】筛选条件
  const [filterSubject, setFilterSubject] = useState<string>('');
  const [filterGrade, setFilterGrade] = useState<string>('');

  // 【V25.0增强】加载错题列表（支持筛选）
  const loadMistakes = async () => {
    try {
      // 构建查询参数
      const params: any = {};
      if (filterSubject) params.subject = filterSubject;
      if (filterGrade) params.grade = filterGrade;
      
      const response = await axios.get(`${API_BASE_URL}/mistakes/`, { params });
      const mistakesList = response.data.items || [];
      setMistakes(mistakesList);
      
      // 提取所有唯一的知识点
      const knowledgePointsSet = new Set<string>();
      mistakesList.forEach((mistake: Mistake) => {
        if (mistake.knowledge_points && Array.isArray(mistake.knowledge_points)) {
          mistake.knowledge_points.forEach(kp => knowledgePointsSet.add(kp));
        }
      });
      setAllKnowledgePoints(Array.from(knowledgePointsSet).sort());
    } catch (error) {
      console.error('加载错题失败:', error);
      alert('加载错题失败');
    }
  };

  // 加载生成的题目
  const loadQuestions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/questions/`);
      setQuestions(response.data.items || []);
    } catch (error) {
      console.error('加载题目失败:', error);
    }
  };

  // 加载统计信息
  const loadStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/mistakes/stats/summary`);
      setStats(response.data);
    } catch (error) {
      console.error('加载统计失败:', error);
    }
  };

  // 删除错题
  const deleteMistake = async (id: string) => {
    if (!confirm('确定要删除这道错题吗？')) return;
    try {
      await axios.delete(`${API_BASE_URL}/mistakes/${id}`);
      await loadMistakes();
      await loadStats();
      alert('删除成功');
    } catch (error) {
      console.error('删除失败:', error);
      alert('删除失败');
    }
  };

  // 【新增】删除生成的题目
  const deleteQuestion = async (id: string) => {
    if (!confirm('确定要删除这道题目吗？')) return;
    try {
      await axios.delete(`${API_BASE_URL}/questions/${id}`);
      await loadQuestions();
      // 如果题目被选中，也要从选中列表中移除
      if (selectedQuestions.has(id)) {
        const newSet = new Set(selectedQuestions);
        newSet.delete(id);
        setSelectedQuestions(newSet);
      }
      alert('删除成功');
    } catch (error) {
      console.error('删除失败:', error);
      alert('删除失败');
    }
  };

  // 生成新题目
  const generateQuestions = async () => {
    if (selectedMistakes.size === 0) {
      alert('请先选择至少一道错题');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/questions/generate`, {
        mistake_ids: Array.from(selectedMistakes),
        count: 3,
        difficulty: '中等',
        allow_web_search: false  // 简单模式默认不开启网络搜索
      }, {
        timeout: 300000  // 延长5倍到300秒（5分钟）
      });
      alert(`成功生成${response.data.questions.length}道题目！`);
      setSelectedMistakes(new Set());
      await loadQuestions();
      setActiveTab('questions');
    } catch (error: any) {
      console.error('生成题目失败:', error);
      if (error.code === 'ECONNABORTED') {
        alert('生成超时，请稍后重试或减少题目数量');
      } else {
        alert('生成题目失败: ' + (error.response?.data?.detail || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  // 基于知识点或错题生成试卷
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
      const response = await axios.post(`${API_BASE_URL}/questions/generate`, {
        mistake_ids: targetMistakeIds,
        count: paperConfig.count,
        difficulty: paperConfig.difficulty,
        allow_web_search: paperConfig.allowWebSearch  // 【V25.0】传递网络搜索设置
      }, {
        timeout: 600000  // 延长5倍到600秒（10分钟），适应大量题目生成
      });
      
      alert(`成功生成${response.data.questions.length}道题目！${paperConfig.allowWebSearch ? '（已使用网络辅助）' : ''}`);
      setSelectedMistakes(new Set());
      setSelectedKnowledgePoints(new Set());
      await loadQuestions();
      setActiveTab('questions');
    } catch (error: any) {
      console.error('生成题目失败:', error);
      if (error.code === 'ECONNABORTED') {
        alert('生成超时，请稍后重试或减少题目数量');
      } else {
        alert('生成题目失败: ' + (error.response?.data?.detail || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  // 【改进】导出为PDF
  const exportPDF = async (questionIds: string[]) => {
    if (questionIds.length === 0) {
      alert('请先选择要导出的题目');
      return;
    }

    try {
      // 显示加载提示
      const originalText = '正在生成PDF...';
      
      const response = await axios.post(`${API_BASE_URL}/export/pdf`, {
        question_ids: questionIds,
        title: '练习题集',
        include_answers: true
      }, {
        responseType: 'blob',  // 重要：接收二进制数据
        timeout: 30000
      });
      
      // 创建下载链接
      const blob = new Blob([response.data], { type: 'application/pdf' });
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
      if (error.code === 'ECONNABORTED') {
        alert('导出超时，请减少题目数量后重试');
      } else {
        alert('导出失败: ' + (error.response?.data?.detail || error.message || '未知错误'));
      }
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

  useEffect(() => {
    loadMistakes();
    loadQuestions();
    loadStats();
  }, []);

  // 【V25.0新增】当筛选条件变化时重新加载
  useEffect(() => {
    loadMistakes();
  }, [filterSubject, filterGrade]);

  // 【已优化】MathJax渲染现在由QuestionItem组件独立处理，无需全局渲染

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* 标题栏 */}
      <div style={{ marginBottom: '20px', textAlign: 'center' }}>
        <h1 style={{ color: '#5C6AC4', marginBottom: '10px' }}>
          🎓 沐梧AI - 智能错题本
        </h1>
        <p style={{ color: '#666' }}>无需登录 · 轻量便捷 · AI助学</p>
      </div>

      {/* 统计信息卡片 */}
      {stats && (
        <div style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '20px',
          borderRadius: '10px',
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-around'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{stats.total_mistakes}</div>
            <div style={{ fontSize: '14px', opacity: 0.9 }}>错题总数</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{questions.length}</div>
            <div style={{ fontSize: '14px', opacity: 0.9 }}>生成题目</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{selectedMistakes.size}</div>
            <div style={{ fontSize: '14px', opacity: 0.9 }}>已选错题</div>
          </div>
        </div>
      )}

      {/* 选项卡 */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', borderBottom: '2px solid #eee', flexWrap: 'wrap' }}>
        <button
          onClick={() => setActiveTab('mistakes')}
          style={{
            padding: '12px 24px',
            border: 'none',
            background: activeTab === 'mistakes' ? '#5C6AC4' : 'transparent',
            color: activeTab === 'mistakes' ? 'white' : '#666',
            cursor: 'pointer',
            borderRadius: '8px 8px 0 0',
            fontWeight: 'bold'
          }}
        >
          📚 错题本 ({mistakes.length})
        </button>
        <button
          onClick={() => setActiveTab('questions')}
          style={{
            padding: '12px 24px',
            border: 'none',
            background: activeTab === 'questions' ? '#5C6AC4' : 'transparent',
            color: activeTab === 'questions' ? 'white' : '#666',
            cursor: 'pointer',
            borderRadius: '8px 8px 0 0',
            fontWeight: 'bold'
          }}
        >
          ✨ 生成的题目 ({questions.length})
        </button>
        <button
          onClick={() => setActiveTab('generate')}
          style={{
            padding: '12px 24px',
            border: 'none',
            background: activeTab === 'generate' ? '#5C6AC4' : 'transparent',
            color: activeTab === 'generate' ? 'white' : '#666',
            cursor: 'pointer',
            borderRadius: '8px 8px 0 0',
            fontWeight: 'bold'
          }}
        >
          🎯 AI出题
        </button>
        <button
          onClick={() => setActiveTab('papergen')}
          style={{
            padding: '12px 24px',
            border: 'none',
            background: activeTab === 'papergen' ? '#5C6AC4' : 'transparent',
            color: activeTab === 'papergen' ? 'white' : '#666',
            cursor: 'pointer',
            borderRadius: '8px 8px 0 0',
            fontWeight: 'bold'
          }}
        >
          📝 智能试卷
        </button>
      </div>

      {/* 错题本标签页 */}
      {activeTab === 'mistakes' && (
        <div>
          <div style={{ marginBottom: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            <h3>我的错题集</h3>
            <button
              onClick={loadMistakes}
              style={{
                padding: '8px 16px',
                background: '#5C6AC4',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer'
              }}
            >
              🔄 刷新
            </button>
          </div>

          {/* 【V25.0新增】筛选器 */}
          {stats && (stats.subjects || stats.grades) && (
            <div style={{
              marginBottom: '20px',
              padding: '15px',
              background: '#f5f5f5',
              borderRadius: '10px'
            }}>
              <h4 style={{ marginBottom: '10px', fontSize: '14px', color: '#666' }}>📊 筛选条件</h4>
              <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
                {/* 学科筛选 */}
                {stats.subjects && Object.keys(stats.subjects).length > 0 && (
                  <div>
                    <label style={{ display: 'block', marginBottom: '5px', fontSize: '13px', fontWeight: 'bold' }}>
                      学科
                    </label>
                    <select
                      value={filterSubject}
                      onChange={(e) => setFilterSubject(e.target.value)}
                      style={{
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        fontSize: '13px',
                        minWidth: '120px'
                      }}
                    >
                      <option value="">全部学科</option>
                      {Object.keys(stats.subjects).map(subject => (
                        <option key={subject} value={subject}>
                          {subject} ({stats.subjects[subject]})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* 年级筛选 */}
                {stats.grades && Object.keys(stats.grades).length > 0 && (
                  <div>
                    <label style={{ display: 'block', marginBottom: '5px', fontSize: '13px', fontWeight: 'bold' }}>
                      年级
                    </label>
                    <select
                      value={filterGrade}
                      onChange={(e) => setFilterGrade(e.target.value)}
                      style={{
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        fontSize: '13px',
                        minWidth: '120px'
                      }}
                    >
                      <option value="">全部年级</option>
                      {Object.keys(stats.grades).map(grade => (
                        <option key={grade} value={grade}>
                          {grade} ({stats.grades[grade]})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* 清除筛选 */}
                {(filterSubject || filterGrade) && (
                  <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                    <button
                      onClick={() => {
                        setFilterSubject('');
                        setFilterGrade('');
                      }}
                      style={{
                        padding: '8px 16px',
                        background: '#ff5252',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '13px'
                      }}
                    >
                      清除筛选
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {mistakes.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '60px 20px',
              color: '#999',
              border: '2px dashed #ddd',
              borderRadius: '10px'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>📝</div>
              <p>还没有错题记录</p>
              <p style={{ fontSize: '14px' }}>在主界面使用"图片解题"功能时，AI会自动保存错题</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '20px' }}>
              {mistakes.map(mistake => (
                <div
                  key={mistake.id}
                  style={{
                    border: '1px solid #ddd',
                    borderRadius: '10px',
                    overflow: 'hidden',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    cursor: 'pointer'
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.transform = 'translateY(-5px)';
                    e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.1)';
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  {/* 图片 */}
                  {mistake.image_base64 && (
                    <img
                      src={`data:image/jpeg;base64,${mistake.image_base64}`}
                      alt="错题图片"
                      style={{ width: '100%', height: '200px', objectFit: 'cover' }}
                    />
                  )}

                  {/* 内容 */}
                  <div style={{ padding: '15px' }}>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginBottom: '10px'
                    }}>
                      <div style={{ display: 'flex', gap: '5px' }}>
                        <span style={{
                          background: '#5C6AC4',
                          color: 'white',
                          padding: '4px 12px',
                          borderRadius: '12px',
                          fontSize: '12px'
                        }}>
                          {mistake.subject}
                        </span>
                        {mistake.grade && mistake.grade !== '未分类' && (
                          <span style={{
                            background: '#FF9800',
                            color: 'white',
                            padding: '4px 12px',
                            borderRadius: '12px',
                            fontSize: '12px'
                          }}>
                            {mistake.grade}
                          </span>
                        )}
                      </div>
                      <span style={{ fontSize: '12px', color: '#999' }}>
                        查看 {mistake.reviewed_count} 次
                      </span>
                    </div>

                    {mistake.question_text && (
                      <p style={{
                        fontSize: '14px',
                        color: '#333',
                        marginBottom: '10px',
                        maxHeight: '60px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                      }}>
                        {mistake.question_text.substring(0, 100)}
                        {mistake.question_text.length > 100 && '...'}
                      </p>
                    )}

                    {mistake.knowledge_points.length > 0 && (
                      <div style={{ marginBottom: '10px' }}>
                        {mistake.knowledge_points.map((kp, idx) => (
                          <span
                            key={idx}
                            style={{
                              display: 'inline-block',
                              background: '#f0f0f0',
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontSize: '12px',
                              marginRight: '5px',
                              marginBottom: '5px'
                            }}
                          >
                            {kp}
                          </span>
                        ))}
                      </div>
                    )}

                    <div style={{
                      fontSize: '12px',
                      color: '#999',
                      marginBottom: '10px'
                    }}>
                      {new Date(mistake.created_at).toLocaleString('zh-CN')}
                    </div>

                    <div style={{ display: 'flex', gap: '10px' }}>
                      <label style={{
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px',
                        cursor: 'pointer',
                        padding: '8px',
                        background: selectedMistakes.has(mistake.id) ? '#e8f5e9' : '#f5f5f5',
                        borderRadius: '5px'
                      }}>
                        <input
                          type="checkbox"
                          checked={selectedMistakes.has(mistake.id)}
                          onChange={(e) => {
                            const newSelected = new Set(selectedMistakes);
                            if (e.target.checked) {
                              newSelected.add(mistake.id);
                            } else {
                              newSelected.delete(mistake.id);
                            }
                            setSelectedMistakes(newSelected);
                          }}
                        />
                        <span style={{ fontSize: '12px' }}>选中</span>
                      </label>
                      <button
                        onClick={() => deleteMistake(mistake.id)}
                        style={{
                          padding: '8px 12px',
                          background: '#ff5252',
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
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 生成的题目标签页 */}
      {activeTab === 'questions' && (
        <div>
          <div style={{ marginBottom: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            <h3>AI生成的题目 {selectedQuestions.size > 0 && `(已选${selectedQuestions.size}道)`}</h3>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              {selectedQuestions.size > 0 && (
                <button
                  onClick={exportSelectedQuestions}
                  style={{
                    padding: '8px 16px',
                    background: '#FF9800',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    fontWeight: 'bold'
                  }}
                >
                  📥 导出选中 ({selectedQuestions.size})
                </button>
              )}
              {questions.length > 0 && (
                <button
                  onClick={() => exportPDF(questions.map(q => q.id))}
                  style={{
                    padding: '8px 16px',
                    background: '#4CAF50',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer'
                  }}
                >
                  📥 导出全部为PDF
                </button>
              )}
              <button
                onClick={loadQuestions}
                style={{
                  padding: '8px 16px',
                  background: '#5C6AC4',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer'
                }}
              >
                🔄 刷新
              </button>
            </div>
          </div>

          {questions.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '60px 20px',
              color: '#999',
              border: '2px dashed #ddd',
              borderRadius: '10px'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '20px' }}>✨</div>
              <p>还没有生成题目</p>
              <p style={{ fontSize: '14px' }}>去"AI出题"标签页基于错题生成练习题</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {questions.map((question, index) => (
                <QuestionItem
                  key={question.id}
                  question={question}
                  index={index}
                  isSelected={selectedQuestions.has(question.id)}
                  onToggleSelect={(id) => {
                    const newSet = new Set(selectedQuestions);
                    if (newSet.has(id)) {
                      newSet.delete(id);
                    } else {
                      newSet.add(id);
                    }
                    setSelectedQuestions(newSet);
                  }}
                  onDelete={deleteQuestion}
                  onExportPDF={exportPDF}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* AI出题标签页 */}
      {activeTab === 'generate' && (
        <div>
          <div style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            padding: '30px',
            borderRadius: '15px',
            textAlign: 'center',
            marginBottom: '30px'
          }}>
            <h2 style={{ margin: '0 0 15px 0' }}>🎯 AI智能出题</h2>
            <p style={{ margin: 0, fontSize: '16px', opacity: 0.9 }}>
              选择错题，AI为你生成针对性练习题
            </p>
          </div>

          <div style={{
            background: '#f5f5f5',
            padding: '20px',
            borderRadius: '10px',
            marginBottom: '20px'
          }}>
            <h3>📋 使用步骤：</h3>
            <ol style={{ paddingLeft: '20px', lineHeight: '2' }}>
              <li>在"错题本"标签页中<strong>勾选</strong>你想要练习的错题</li>
              <li>返回此页面，点击"<strong>开始生成</strong>"按钮</li>
              <li>AI将分析错题，生成3道针对性练习题</li>
              <li>在"生成的题目"标签页查看和导出题目</li>
            </ol>
          </div>

          <div style={{
            textAlign: 'center',
            padding: '40px',
            border: '2px dashed #5C6AC4',
            borderRadius: '15px'
          }}>
            <div style={{
              fontSize: '64px',
              marginBottom: '20px'
            }}>
              {selectedMistakes.size > 0 ? '✅' : '📝'}
            </div>
            <h3 style={{ marginBottom: '15px' }}>
              {selectedMistakes.size > 0
                ? `已选择 ${selectedMistakes.size} 道错题`
                : '请先选择错题'}
            </h3>
            <button
              onClick={generateQuestions}
              disabled={loading || selectedMistakes.size === 0}
              style={{
                padding: '15px 40px',
                fontSize: '18px',
                background: selectedMistakes.size > 0 ? '#5C6AC4' : '#ccc',
                color: 'white',
                border: 'none',
                borderRadius: '10px',
                cursor: selectedMistakes.size > 0 ? 'pointer' : 'not-allowed',
                transition: 'all 0.3s',
                fontWeight: 'bold'
              }}
            >
              {loading ? '⏳ 生成中...' : '✨ 开始生成'}
            </button>
          </div>

          {selectedMistakes.size > 0 && (
            <div style={{ marginTop: '20px', textAlign: 'center' }}>
              <p style={{ color: '#666', fontSize: '14px' }}>
                💡 生成时间约需 5-10 秒，请耐心等待
              </p>
            </div>
          )}
        </div>
      )}

      {/* 智能试卷标签页 */}
      {activeTab === 'papergen' && (
        <div>
          <div style={{
            background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            color: 'white',
            padding: '30px',
            borderRadius: '15px',
            marginBottom: '30px'
          }}>
            <h2 style={{ marginBottom: '10px' }}>📝 智能试卷生成</h2>
            <p style={{ opacity: 0.9, fontSize: '14px' }}>
              基于错题或知识点，生成个性化专属练习试卷，题目和解析分开显示
            </p>
          </div>

          {/* 选择模式 */}
          <div style={{
            background: '#f5f5f5',
            padding: '20px',
            borderRadius: '10px',
            marginBottom: '20px'
          }}>
            <h3 style={{ marginBottom: '15px' }}>📌 第一步：选择生成依据</h3>
            
            {/* 方式1：按知识点选择 */}
            <div style={{
              background: 'white',
              padding: '20px',
              borderRadius: '8px',
              marginBottom: '15px',
              border: selectedKnowledgePoints.size > 0 ? '2px solid #5C6AC4' : '1px solid #ddd'
            }}>
              <h4 style={{ marginBottom: '10px', color: '#5C6AC4' }}>方式1：按知识点选择</h4>
              <p style={{ fontSize: '13px', color: '#666', marginBottom: '15px' }}>
                选择一个或多个知识点，系统会找到相关的所有错题并生成练习
              </p>
              
              {allKnowledgePoints.length === 0 ? (
                <p style={{ color: '#999', fontSize: '14px' }}>暂无知识点（请先在错题本中添加错题）</p>
              ) : (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {allKnowledgePoints.map(kp => (
                    <button
                      key={kp}
                      onClick={() => {
                        const newSet = new Set(selectedKnowledgePoints);
                        if (newSet.has(kp)) {
                          newSet.delete(kp);
                        } else {
                          newSet.add(kp);
                        }
                        setSelectedKnowledgePoints(newSet);
                        // 清空错题选择
                        setSelectedMistakes(new Set());
                      }}
                      style={{
                        padding: '8px 16px',
                        border: selectedKnowledgePoints.has(kp) ? '2px solid #5C6AC4' : '1px solid #ddd',
                        background: selectedKnowledgePoints.has(kp) ? '#e8eaf6' : 'white',
                        borderRadius: '20px',
                        cursor: 'pointer',
                        fontSize: '13px',
                        fontWeight: selectedKnowledgePoints.has(kp) ? 'bold' : 'normal',
                        color: selectedKnowledgePoints.has(kp) ? '#5C6AC4' : '#666'
                      }}
                    >
                      {selectedKnowledgePoints.has(kp) ? '✓ ' : ''}{kp}
                    </button>
                  ))}
                </div>
              )}
              {selectedKnowledgePoints.size > 0 && (
                <p style={{ marginTop: '10px', fontSize: '13px', color: '#5C6AC4' }}>
                  ✓ 已选择 {selectedKnowledgePoints.size} 个知识点
                </p>
              )}
            </div>

            {/* 方式2：按错题选择 */}
            <div style={{
              background: 'white',
              padding: '20px',
              borderRadius: '8px',
              border: selectedMistakes.size > 0 ? '2px solid #5C6AC4' : '1px solid #ddd'
            }}>
              <h4 style={{ marginBottom: '10px', color: '#5C6AC4' }}>方式2：直接选择错题</h4>
              <p style={{ fontSize: '13px', color: '#666', marginBottom: '10px' }}>
                在"错题本"标签页中勾选具体的错题，然后回到此页面生成
              </p>
              {selectedMistakes.size > 0 ? (
                <p style={{ fontSize: '13px', color: '#5C6AC4' }}>
                  ✓ 已在错题本中选择 {selectedMistakes.size} 道错题
                </p>
              ) : (
                <p style={{ fontSize: '13px', color: '#999' }}>
                  前往"错题本"标签页选择错题
                </p>
              )}
            </div>
          </div>

          {/* 试卷参数配置 */}
          <div style={{
            background: '#f5f5f5',
            padding: '20px',
            borderRadius: '10px',
            marginBottom: '20px'
          }}>
            <h3 style={{ marginBottom: '15px' }}>⚙️ 第二步：设置试卷参数</h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
              {/* 题目数量 */}
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', fontSize: '14px' }}>
                  题目数量
                </label>
                <select
                  value={paperConfig.count}
                  onChange={(e) => setPaperConfig({...paperConfig, count: Number(e.target.value)})}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                >
                  <option value={3}>3题</option>
                  <option value={5}>5题</option>
                  <option value={8}>8题</option>
                  <option value={10}>10题</option>
                  <option value={15}>15题</option>
                  <option value={20}>20题</option>
                </select>
              </div>

              {/* 难度 */}
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', fontSize: '14px' }}>
                  难度等级
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
                  <option value="混合">混合难度</option>
                </select>
              </div>

              {/* 题型 */}
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', fontSize: '14px' }}>
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

            {/* 【V25.0新增】网络辅助出题选项 */}
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
                生成后可在"生成的题目"标签页查看和导出
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
              <li>生成后的题目会显示在"生成的题目"标签页，包含详细解析</li>
              <li>可以勾选多道题目，一键导出为Markdown文件打印使用</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimpleMistakeBook;

