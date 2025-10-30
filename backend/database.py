"""
==============================================================================
沐梧AI解题系统 - MySQL数据库连接模块 (V25.1)
==============================================================================
功能：
- 数据库连接池管理
- 用户认证（注册/登录）
- 数据CRUD操作
- 错题与题目管理

数据库：
- 连接：14.103.127.20:3306
- 数据库：edu
- 用户：root
- 密码：Jiuzhi#2024
==============================================================================
"""

import pymysql
from pymysql import cursors
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
import hashlib
import uuid
import os
from datetime import datetime

# ==============================================================================
# 数据库配置
# ==============================================================================

DB_CONFIG = {
    'host': '14.103.127.20',
    'port': 3306,
    'user': 'root',
    'password': 'Jiuzhi#2024',
    'database': 'edu',
    'charset': 'utf8mb4',
    'cursorclass': cursors.DictCursor,  # 返回字典格式
    'autocommit': True,  # 自动提交
    'connect_timeout': 10,  # 连接超时（秒）
    'read_timeout': 30,  # 读取超时（秒）
    'write_timeout': 30  # 写入超时（秒）
}

# ==============================================================================
# 连接池管理
# ==============================================================================

class DatabasePool:
    """
    数据库连接池（简化版）
    实际生产环境建议使用 DBUtils.PooledDB
    """
    
    def __init__(self, config: Dict[str, Any], pool_size: int = 5):
        self.config = config
        self.pool_size = pool_size
        self._connections = []
        self._initialize_pool()
    
    def _initialize_pool(self):
        """初始化连接池"""
        try:
            for _ in range(self.pool_size):
                conn = pymysql.connect(**self.config)
                self._connections.append(conn)
            print(f"✅ 数据库连接池初始化成功 ({self.pool_size}个连接)")
        except Exception as e:
            print(f"❌ 数据库连接池初始化失败: {e}")
            raise
    
    def get_connection(self):
        """获取一个连接（带健康检查）"""
        # 尝试从池中获取连接
        while self._connections:
            conn = self._connections.pop()
            try:
                # 检查连接是否仍然有效
                conn.ping(reconnect=True)
                return conn
            except Exception as e:
                print(f"⚠️  连接失效，已丢弃: {e}")
                try:
                    conn.close()
                except:
                    pass
        
        # 池耗尽或所有连接失效时创建新连接
        print("🔄 创建新的数据库连接...")
        return pymysql.connect(**self.config)
    
    def return_connection(self, conn):
        """归还连接到池（检查连接健康）"""
        try:
            # 检查连接是否健康
            conn.ping(reconnect=False)
            
            if len(self._connections) < self.pool_size:
                self._connections.append(conn)
            else:
                conn.close()
        except Exception as e:
            # 连接已失效，直接关闭
            print(f"⚠️  归还的连接已失效，已丢弃: {e}")
            try:
                conn.close()
            except:
                pass
    
    def close_all(self):
        """关闭所有连接"""
        for conn in self._connections:
            conn.close()
        self._connections.clear()


# 全局连接池实例
_db_pool: Optional[DatabasePool] = None


def init_database_pool():
    """初始化全局数据库连接池"""
    global _db_pool
    if _db_pool is None:
        _db_pool = DatabasePool(DB_CONFIG)
    return _db_pool


@contextmanager
def get_db_connection():
    """
    上下文管理器：获取数据库连接
    
    用法:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user")
            results = cursor.fetchall()
    """
    if _db_pool is None:
        init_database_pool()
    
    conn = _db_pool.get_connection()
    try:
        yield conn
    finally:
        _db_pool.return_connection(conn)


# ==============================================================================
# 工具函数
# ==============================================================================

def hash_password(password: str) -> str:
    """密码加密（SHA256 + 盐值）"""
    salt = "muwu_ai_solver_2024"  # 盐值（实际应用中应该为每个用户生成独立盐值）
    return hashlib.sha256((password + salt).encode()).hexdigest()


def generate_user_id() -> str:
    """生成用户ID"""
    return str(uuid.uuid4())


def generate_exam_id() -> str:
    """生成试卷ID"""
    return str(uuid.uuid4())


def generate_subject_id() -> str:
    """生成题目ID"""
    return str(uuid.uuid4())


# ==============================================================================
# 用户管理
# ==============================================================================

class UserManager:
    """用户管理类"""
    
    @staticmethod
    def register(account: str, password: str) -> Dict[str, Any]:
        """
        用户注册
        
        Args:
            account: 用户账号
            password: 明文密码
        
        Returns:
            {"success": bool, "user_id": str, "message": str}
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 检查账号是否已存在
            cursor.execute("SELECT user_id FROM user WHERE account = %s", (account,))
            if cursor.fetchone():
                return {"success": False, "message": "账号已存在"}
            
            # 创建新用户
            user_id = generate_user_id()
            pwd_hash = hash_password(password)
            temp_uuid = str(uuid.uuid4())
            
            try:
                cursor.execute(
                    "INSERT INTO user (user_id, account, pwd, temp_uuid) VALUES (%s, %s, %s, %s)",
                    (user_id, account, pwd_hash, temp_uuid)
                )
                
                print(f"✅ 用户注册成功: {account} (ID: {user_id})")
                return {"success": True, "user_id": user_id, "message": "注册成功"}
            
            except Exception as e:
                print(f"❌ 用户注册失败: {e}")
                return {"success": False, "message": f"注册失败: {str(e)}"}
    
    @staticmethod
    def login(account: str, password: str) -> Dict[str, Any]:
        """
        用户登录
        
        Args:
            account: 用户账号
            password: 明文密码
        
        Returns:
            {"success": bool, "user_id": str, "account": str, "nickname": str, "message": str}
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            pwd_hash = hash_password(password)
            cursor.execute(
                "SELECT user_id, account FROM user WHERE account = %s AND pwd = %s",
                (account, pwd_hash)
            )
            
            user = cursor.fetchone()
            if user:
                print(f"✅ 用户登录成功: {account} (ID: {user['user_id']})")
                return {
                    "success": True,
                    "user_id": user['user_id'],
                    "account": user['account'],
                    "nickname": user['account'],  # 使用account作为昵称
                    "message": "登录成功"
                }
            else:
                return {"success": False, "message": "账号或密码错误"}
    
    @staticmethod
    def get_user_info(user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            {"user_id": str, "account": str} 或 None
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, account FROM user WHERE user_id = %s",
                (user_id,)
            )
            return cursor.fetchone()


# ==============================================================================
# 题目管理
# ==============================================================================

class SubjectManager:
    """题目管理类"""
    
    @staticmethod
    def create_subject(
        subject_title: str,
        subject_desc: Optional[str] = None,
        image_url: Optional[str] = None,
        solve: Optional[str] = None,
        answer: Optional[str] = None,
        subject_type: Optional[str] = None,
        subject_name: Optional[str] = None,
        knowledge_points: Optional[str] = None,
        difficulty: Optional[str] = None,
        grade: Optional[str] = None
    ) -> str:
        """
        创建题目
        
        Args:
            subject_title: 题目标题
            subject_desc: 题目描述
            image_url: 图片URL
            solve: 解答过程
            answer: 答案
            subject_type: 题目类型（如：generated, mistake等）
            subject_name: 学科名称
            knowledge_points: 知识点（JSON字符串）
            difficulty: 难度
            grade: 年级
        
        Returns:
            subject_id: 题目ID
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            subject_id = generate_subject_id()
            
            cursor.execute(
                """INSERT INTO subject (
                    subject_id, subject_title, subject_desc, image_url, solve, answer,
                    subject_type, subject_name, knowledge_points, difficulty, grade
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (subject_id, subject_title, subject_desc, image_url, solve, answer,
                 subject_type, subject_name, knowledge_points, difficulty, grade)
            )
            
            print(f"✅ 题目创建成功: {subject_id} ({subject_type or '普通题目'})")
            return subject_id
    
    @staticmethod
    def get_subject(subject_id: str) -> Optional[Dict[str, Any]]:
        """获取题目详情"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM subject WHERE subject_id = %s",
                (subject_id,)
            )
            return cursor.fetchone()
    
    @staticmethod
    def get_user_subjects(user_id: str, exam_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取用户的题目列表（通过user_exam关联）
        
        Args:
            user_id: 用户ID
            exam_id: 试卷ID（可选，用于筛选特定试卷的题目）
        
        Returns:
            题目列表
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if exam_id:
                query = """
                    SELECT s.* FROM subject s
                    JOIN user_exam ue ON s.subject_id = ue.subject_id
                    WHERE ue.user_info = %s AND ue.exam_id = %s
                """
                cursor.execute(query, (user_id, exam_id))
            else:
                query = """
                    SELECT DISTINCT s.* FROM subject s
                    JOIN user_exam ue ON s.subject_id = ue.subject_id
                    WHERE ue.user_info = %s
                """
                cursor.execute(query, (user_id,))
            
            return cursor.fetchall()


# ==============================================================================
# 试卷管理
# ==============================================================================

class ExamManager:
    """试卷管理类"""
    
    @staticmethod
    def create_exam(exam_title: str, exam_content: Optional[str] = None) -> str:
        """
        创建试卷
        
        Returns:
            exam_id: 试卷ID
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            exam_id = generate_exam_id()
            
            cursor.execute(
                """INSERT INTO exam (exam_id, exam_title, exam_content)
                   VALUES (%s, %s, %s)""",
                (exam_id, exam_title, exam_content)
            )
            
            print(f"✅ 试卷创建成功: {exam_id} - {exam_title}")
            return exam_id
    
    @staticmethod
    def get_user_exams(user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有试卷"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT DISTINCT e.* FROM exam e
                JOIN user_exam ue ON e.exam_id = ue.exam_id
                WHERE ue.user_info = %s
            """
            cursor.execute(query, (user_id,))
            
            return cursor.fetchall()
    
    @staticmethod
    def link_user_exam_subject(user_id: str, exam_id: str, subject_id: str) -> str:
        """
        建立用户-试卷-题目关联
        
        Returns:
            record_id: 记录ID
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            record_id = str(uuid.uuid4())
            
            cursor.execute(
                """INSERT INTO user_exam (id, user_info, subject_id, exam_id)
                   VALUES (%s, %s, %s, %s)""",
                (record_id, user_id, subject_id, exam_id)
            )
            
            return record_id


# ==============================================================================
# 对话历史管理 (V25.2新增)
# ==============================================================================

class ChatManager:
    """对话历史管理类"""
    
    @staticmethod
    def create_session(
        user_id: str,
        title: str = "新对话",
        mode: str = "solve",
        subject: str = "未分类",
        grade: str = "未分类"
    ) -> str:
        """
        创建新的对话会话
        
        Returns:
            session_id: 会话ID
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            session_id = str(uuid.uuid4())
            
            cursor.execute(
                """INSERT INTO chat_session (session_id, user_id, title, mode, subject, grade)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (session_id, user_id, title, mode, subject, grade)
            )
            
            print(f"✅ 对话会话创建成功: {session_id}")
            return session_id
    
    @staticmethod
    def add_message(
        session_id: str,
        role: str,
        content: str,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        message_type: str = "text"
    ) -> int:
        """
        添加一条对话消息
        
        Args:
            session_id: 会话ID
            role: 角色（user/assistant）
            content: 消息内容
            image_url: 图片URL（可选）
            image_base64: 图片Base64（可选）
            message_type: 消息类型（text/image/mixed）
        
        Returns:
            message_id: 消息ID
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO chat_history (session_id, role, content, image_url, image_base64, message_type)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (session_id, role, content, image_url, image_base64, message_type)
            )
            
            return cursor.lastrowid
    
    @staticmethod
    def get_session_history(session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取会话的历史消息
        
        Args:
            session_id: 会话ID
            limit: 返回消息数量限制
        
        Returns:
            消息列表（按时间升序）
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT id, role, content, image_url, message_type, created_at
                   FROM chat_history
                   WHERE session_id = %s
                   ORDER BY created_at ASC
                   LIMIT %s""",
                (session_id, limit)
            )
            
            return cursor.fetchall()
    
    @staticmethod
    def get_user_sessions(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取用户的所有会话列表
        
        Args:
            user_id: 用户ID
            limit: 返回会话数量限制
        
        Returns:
            会话列表（按更新时间降序）
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT session_id, title, mode, subject, grade, created_at, updated_at
                   FROM chat_session
                   WHERE user_id = %s AND is_deleted = 0
                   ORDER BY updated_at DESC
                   LIMIT %s""",
                (user_id, limit)
            )
            
            return cursor.fetchall()
    
    @staticmethod
    def update_session_title(session_id: str, title: str) -> bool:
        """更新会话标题"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE chat_session SET title = %s WHERE session_id = %s",
                (title, session_id)
            )
            
            return cursor.rowcount > 0
    
    @staticmethod
    def delete_session(session_id: str, soft_delete: bool = True) -> bool:
        """
        删除会话（支持软删除和硬删除）
        
        Args:
            session_id: 会话ID
            soft_delete: True=软删除（标记删除），False=硬删除（物理删除）
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if soft_delete:
                cursor.execute(
                    "UPDATE chat_session SET is_deleted = 1 WHERE session_id = %s",
                    (session_id,)
                )
            else:
                # 硬删除（会级联删除历史消息）
                cursor.execute(
                    "DELETE FROM chat_session WHERE session_id = %s",
                    (session_id,)
                )
            
            return cursor.rowcount > 0
    
    @staticmethod
    def get_session_info(session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话详情"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT * FROM chat_session 
                   WHERE session_id = %s AND is_deleted = 0""",
                (session_id,)
            )
            
            return cursor.fetchone()


# ==============================================================================
# 错题本管理增强 (V25.2新增)
# ==============================================================================

class MistakeManager:
    """错题本管理类（增强版）"""
    
    @staticmethod
    def save_mistake(
        user_id: str,
        subject_title: str,
        subject_desc: str,
        image_url: Optional[str] = None,
        user_mistake_text: Optional[str] = None,
        correct_answer: Optional[str] = None,
        explanation: Optional[str] = None,
        knowledge_points: Optional[List[str]] = None,
        subject_name: str = "未分类",
        grade: str = "未分类",
        difficulty: str = "中等",
        mistake_analysis: Optional[str] = None
    ) -> str:
        """
        保存错题到错题本
        
        Args:
            user_id: 用户ID
            subject_title: 题目标题
            subject_desc: 题目描述
            image_url: 题目图片URL
            user_mistake_text: 用户的错误答案
            correct_answer: 正确答案
            explanation: 题目解析
            knowledge_points: 知识点列表
            subject_name: 学科
            grade: 年级
            difficulty: 难度
            mistake_analysis: 错题分析
        
        Returns:
            subject_id: 题目ID
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            subject_id = generate_subject_id()
            exam_id = generate_exam_id()
            
            # 转换知识点为JSON格式
            import json
            knowledge_points_json = json.dumps(knowledge_points, ensure_ascii=False) if knowledge_points else None
            
            # 1. 创建题目
            cursor.execute(
                """INSERT INTO subject (
                    subject_id, subject_title, subject_desc, image_url, 
                    answer, explanation, knowledge_points,
                    subject_type, subject_name, grade, difficulty,
                    user_mistake_text, mistake_analysis, solve
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    subject_id, subject_title, subject_desc, image_url,
                    correct_answer, explanation, knowledge_points_json,
                    'mistake', subject_name, grade, difficulty,
                    user_mistake_text, mistake_analysis, explanation  # solve字段也存解析
                )
            )
            
            # 2. 创建错题本试卷（如果不存在）
            cursor.execute(
                """SELECT exam_id FROM exam 
                   WHERE exam_type = 'mistake_book' AND exam_title = %s
                   LIMIT 1""",
                (f"{user_id}_错题本",)
            )
            existing_exam = cursor.fetchone()
            
            if existing_exam:
                exam_id = existing_exam['exam_id']
            else:
                cursor.execute(
                    """INSERT INTO exam (exam_id, exam_title, exam_type, exam_content, subject, grade)
                       VALUES (%s, %s, 'mistake_book', '自动收集的错题', %s, %s)""",
                    (exam_id, f"{user_id}_错题本", subject_name, grade)
                )
            
            # 3. 关联用户-试卷-题目
            record_id = str(uuid.uuid4())
            cursor.execute(
                """INSERT INTO user_exam (id, user_info, subject_id, exam_id, user_answer, status)
                   VALUES (%s, %s, %s, %s, %s, 'incorrect')""",
                (record_id, user_id, subject_id, exam_id, user_mistake_text)
            )
            
            print(f"✅ 错题保存成功: {subject_id} - {subject_title[:30]}")
            return subject_id
    
    @staticmethod
    def get_user_mistakes(
        user_id: str,
        subject_name: Optional[str] = None,
        grade: Optional[str] = None,
        knowledge_point: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取用户的错题列表（支持筛选）
        
        Args:
            user_id: 用户ID
            subject_name: 学科（可选）
            grade: 年级（可选）
            knowledge_point: 知识点（可选）
            limit: 返回数量限制
        
        Returns:
            错题列表
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT DISTINCT s.*, ue.user_answer, ue.answered_at
                FROM subject s
                JOIN user_exam ue ON s.subject_id = ue.subject_id
                WHERE ue.user_info = %s 
                AND s.subject_type = 'mistake'
            """
            params = [user_id]
            
            if subject_name:
                query += " AND s.subject_name = %s"
                params.append(subject_name)
            
            if grade:
                query += " AND s.grade = %s"
                params.append(grade)
            
            if knowledge_point:
                query += " AND s.knowledge_points LIKE %s"
                params.append(f"%{knowledge_point}%")
            
            query += " ORDER BY ue.answered_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            raw_mistakes = cursor.fetchall()
            
            # 【修复】格式化返回数据，确保包含完整图片和解析
            import json
            formatted_mistakes = []
            for m in raw_mistakes:
                # 提取完整的图片base64（移除data URI前缀）
                image_data = ""
                if m.get('image_url'):
                    if m['image_url'].startswith('data:image'):
                        # 移除 "data:image/jpeg;base64," 前缀
                        image_data = m['image_url'].split(',', 1)[1] if ',' in m['image_url'] else m['image_url']
                    else:
                        image_data = m['image_url']
                
                formatted_mistakes.append({
                    "subject_id": m['subject_id'],
                    "question_text": m.get('subject_desc') or m.get('subject_title') or "错题",
                    "image_base64": image_data,
                    "image_url": m.get('image_url'),  # 保留原始URL
                    "user_mistake_text": m.get('user_mistake_text') or m.get('user_answer') or "",
                    "correct_answer": m.get('answer') or "",
                    "ai_analysis": m.get('solve') or m.get('explanation') or m.get('mistake_analysis') or "",
                    "knowledge_points": json.loads(m['knowledge_points']) if m.get('knowledge_points') else [],
                    "subject_name": m.get('subject_name') or "未分类",
                    "grade": m.get('grade') or "未分类",
                    "difficulty": m.get('difficulty') or "中等",
                    "review_count": m.get('review_count') or 0,
                    "last_review_at": m['last_review_at'].isoformat() if m.get('last_review_at') else None,
                    "created_at": m['created_at'].isoformat() if m.get('created_at') else "",
                })
            
            return formatted_mistakes
    
    @staticmethod
    def update_review_status(subject_id: str) -> bool:
        """更新错题的复习状态"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """UPDATE subject 
                   SET review_count = review_count + 1,
                       last_review_at = CURRENT_TIMESTAMP
                   WHERE subject_id = %s""",
                (subject_id,)
            )
            
            return cursor.rowcount > 0
    
    @staticmethod
    def get_mistake_stats(user_id: str) -> Dict[str, Any]:
        """获取用户错题统计"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 总体统计
            cursor.execute(
                """SELECT 
                    COUNT(*) as total_mistakes,
                    COUNT(DISTINCT s.subject_name) as subject_count,
                    COUNT(DISTINCT s.grade) as grade_count,
                    SUM(s.review_count) as total_reviews
                FROM subject s
                JOIN user_exam ue ON s.subject_id = ue.subject_id
                WHERE ue.user_info = %s AND s.subject_type = 'mistake'""",
                (user_id,)
            )
            overall = cursor.fetchone()
            
            # 按学科统计
            cursor.execute(
                """SELECT 
                    s.subject_name,
                    COUNT(*) as count,
                    AVG(s.review_count) as avg_reviews
                FROM subject s
                JOIN user_exam ue ON s.subject_id = ue.subject_id
                WHERE ue.user_info = %s AND s.subject_type = 'mistake'
                GROUP BY s.subject_name
                ORDER BY count DESC""",
                (user_id,)
            )
            by_subject = cursor.fetchall()
            
            return {
                "overall": overall,
                "by_subject": by_subject
            }


# ==============================================================================
# 数据库初始化与测试
# ==============================================================================

def test_database_connection():
    """测试数据库连接"""
    print("\n" + "="*70)
    print("【数据库连接测试】")
    print("="*70)
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 测试连接
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL版本: {version}")
            
            # 检查表是否存在
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"✅ 数据库表: {[list(t.values())[0] for t in tables]}")
            
            return True
    
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False


if __name__ == "__main__":
    # 测试代码
    if test_database_connection():
        print("\n✅ 数据库模块正常")
    else:
        print("\n❌ 数据库模块异常")
