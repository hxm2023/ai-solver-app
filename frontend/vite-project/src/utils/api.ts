/**
 * ==============================================================================
 * API请求工具 - 自动添加JWT令牌
 * ==============================================================================
 * 功能：
 * - 自动从localStorage读取JWT令牌
 * - 自动添加到请求头
 * - 处理401错误（令牌过期/无效）
 * ==============================================================================
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

/**
 * 获取存储的访问令牌
 */
export const getAccessToken = (): string | null => {
  return localStorage.getItem('access_token');
};

/**
 * 清除认证信息
 */
export const clearAuth = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user_info');
};

/**
 * 获取用户信息
 */
export const getUserInfo = (): any | null => {
  const userInfoStr = localStorage.getItem('user_info');
  if (!userInfoStr) return null;
  
  try {
    return JSON.parse(userInfoStr);
  } catch {
    return null;
  }
};

/**
 * 检查是否已登录
 */
export const isAuthenticated = (): boolean => {
  return !!getAccessToken();
};

/**
 * 创建带认证的fetch请求
 */
export const authenticatedFetch = async (
  url: string,
  options: RequestInit = {}
): Promise<Response> => {
  const token = getAccessToken();
  
  // 添加Authorization头
  const headers = new Headers(options.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  // 合并选项
  const fetchOptions: RequestInit = {
    ...options,
    headers,
  };

  // 完整URL
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

  try {
    const response = await fetch(fullUrl, fetchOptions);

    // 处理401错误（未授权）
    if (response.status === 401) {
      clearAuth();
      // 触发重新登录
      window.dispatchEvent(new CustomEvent('auth:unauthorized'));
    }

    return response;
  } catch (error) {
    console.error('API请求错误:', error);
    throw error;
  }
};

/**
 * API辅助函数
 */
export const api = {
  // GET请求
  get: async (url: string) => {
    const response = await authenticatedFetch(url, {
      method: 'GET',
    });
    return response.json();
  },

  // POST请求（JSON）
  post: async (url: string, data: any) => {
    const response = await authenticatedFetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  // PUT请求
  put: async (url: string, data: any) => {
    const response = await authenticatedFetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  // DELETE请求
  delete: async (url: string) => {
    const response = await authenticatedFetch(url, {
      method: 'DELETE',
    });
    return response.json();
  },

  // POST请求（FormData，用于文件上传）
  postFormData: async (url: string, formData: FormData) => {
    const response = await authenticatedFetch(url, {
      method: 'POST',
      body: formData,
    });
    return response.json();
  },
};

/**
 * 错题本API
 */
export const mistakesApi = {
  // 获取错题列表
  getAll: (params?: { subject?: string; grade?: string; limit?: number; offset?: number }) => {
    const queryParams = new URLSearchParams();
    if (params?.subject) queryParams.set('subject', params.subject);
    if (params?.grade) queryParams.set('grade', params.grade);
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.offset) queryParams.set('offset', params.offset.toString());
    
    const query = queryParams.toString();
    return api.get(`/mistakes/${query ? '?' + query : ''}`);
  },

  // 创建错题
  create: (data: any) => api.post('/mistakes/', data),

  // 删除错题
  delete: (id: string) => api.delete(`/mistakes/${id}`),

  // 获取统计
  getStats: () => api.get('/mistakes/stats/summary'),
};

/**
 * 题目API
 */
export const questionsApi = {
  // 获取题目列表
  getAll: (params?: { subject?: string; grade?: string; limit?: number; offset?: number }) => {
    const queryParams = new URLSearchParams();
    if (params?.subject) queryParams.set('subject', params.subject);
    if (params?.grade) queryParams.set('grade', params.grade);
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.offset) queryParams.set('offset', params.offset.toString());
    
    const query = queryParams.toString();
    return api.get(`/questions/${query ? '?' + query : ''}`);
  },

  // 生成题目
  generate: (data: any) => api.post('/questions/generate', data),

  // 删除题目
  delete: (id: string) => api.delete(`/questions/${id}`),
};

/**
 * 认证API（不需要令牌）
 */
export const authApi = {
  // 注册
  register: async (account: string, password: string, nickname: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ account, password, nickname }),
    });
    return response.json();
  },

  // 登录
  login: async (account: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ account, password }),
    });
    return response.json();
  },

  // 验证令牌
  verify: () => api.get('/auth/verify'),

  // 获取当前用户信息
  me: () => api.get('/auth/me'),
};

/**
 * ==============================================================================
 * V25.2 新增API - 连续对话、错题本增强、试卷生成
 * ==============================================================================
 */

/**
 * 连续对话API
 */
export const chatApi = {
  // 创建新会话
  createSession: (data: {
    title?: string;
    mode: string;
    subject?: string;
    grade?: string;
  }) => api.post('/api/v2/chat/session/create', data),

  // 获取用户所有会话
  getSessions: (limit: number = 50) => 
    api.get(`/api/v2/chat/sessions?limit=${limit}`),

  // 获取会话历史记录
  getHistory: (sessionId: string, limit: number = 100) =>
    api.get(`/api/v2/chat/session/${sessionId}/history?limit=${limit}`),

  // 发送消息（连续对话）
  sendMessage: (data: {
    session_id?: string;
    prompt: string;
    image_base64?: string;
    mode: string;
    subject?: string;
    grade?: string;
  }) => api.post('/api/v2/chat', data),

  // 删除会话
  deleteSession: (sessionId: string) =>
    api.delete(`/api/v2/chat/session/${sessionId}`),
};

/**
 * 错题本增强API（V25.2）
 */
export const mistakesApiV2 = {
  // 获取错题列表（支持筛选）
  getAll: (params?: { 
    subject_name?: string; 
    grade?: string; 
    knowledge_point?: string;
    limit?: number;
  }) => {
    const queryParams = new URLSearchParams();
    if (params?.subject_name) queryParams.set('subject_name', params.subject_name);
    if (params?.grade) queryParams.set('grade', params.grade);
    if (params?.knowledge_point) queryParams.set('knowledge_point', params.knowledge_point);
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    
    const query = queryParams.toString();
    return api.get(`/api/v2/mistakes${query ? '?' + query : ''}`);
  },

  // 手动保存错题
  save: (data: {
    subject_title: string;
    subject_desc: string;
    image_base64?: string;
    user_mistake_text?: string;
    correct_answer?: string;
    explanation?: string;
    knowledge_points?: string[];
    subject_name?: string;
    grade?: string;
    difficulty?: string;
  }) => api.post('/api/v2/mistakes/save', data),

  // 获取错题统计
  getStats: () => api.get('/api/v2/mistakes/stats'),

  // 标记为已复习
  markReviewed: (subjectId: string) =>
    api.post(`/api/v2/mistakes/${subjectId}/review`, {}),
};

/**
 * 试卷生成API（V25.2）
 */
export const paperApiV2 = {
  // 生成试卷（支持学科年级选择）
  generate: (data: {
    subject: string;
    grade: string;
    paper_title: string;
    question_types: string[];
    difficulty?: string;
    total_score?: number;
    duration_minutes?: number;
    knowledge_points?: string[];
  }) => api.post('/api/v2/papers/generate', data),
};

