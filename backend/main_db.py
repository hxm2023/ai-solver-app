"""
==============================================================================
沐梧AI解题系统 - 数据库版本API (V25.1)
==============================================================================
功能：
- 完整的用户认证系统（JWT）
- MySQL数据库存储
- 错题本管理
- AI智能出题
- 保留原有解题功能
==============================================================================
"""

import os
import base64
import asyncio
import tempfile
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.responses import PlainTextResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import dashscope
from dotenv import load_dotenv

# 导入数据库模块
from database import (
    init_database_pool,
    UserManager,
    SubjectManager,
    ExamManager,
    ChatManager,
    MistakeManager,
    get_db_connection
)

# 导入认证模块
from auth_api import router as auth_router, get_current_user

# 导入图像增强模块
from image_enhancer import advanced_image_processing_pipeline

# ==============================================================================
# 初始化
# ==============================================================================

# 加载环境变量（指定.env文件路径）
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# 设置API密钥
import os
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')
if dashscope.api_key:
    print(f"✅ API密钥已加载: {dashscope.api_key[:10]}...")
else:
    print("❌ 警告：未找到API密钥，请检查.env文件")

app = FastAPI(title="沐梧AI - 数据库版本", version="V25.1")

# 初始化数据库连接池
init_database_pool()

# CORS配置 - 允许前端跨域访问
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 注册认证路由
app.include_router(auth_router)

# ==============================================================================
# 数据模型
# ==============================================================================

class MistakeCreate(BaseModel):
    """创建错题请求"""
    image_base64: str
    question_text: Optional[str] = ""
    wrong_answer: Optional[str] = ""
    ai_analysis: Optional[str] = ""
    subject: Optional[str] = "未分类"
    grade: Optional[str] = "未分类"
    knowledge_points: Optional[List[str]] = []

class MistakeResponse(BaseModel):
    """错题响应"""
    id: str
    image_base64: str
    question_text: str
    wrong_answer: str
    ai_analysis: str
    subject: str
    grade: str
    knowledge_points: List[str]
    created_at: str
    reviewed_count: int

class QuestionGenerateRequest(BaseModel):
    """生成题目请求"""
    mistake_ids: List[str]
    count: int = 3
    difficulty: str = "中等"
    allow_web_search: bool = False

class QuestionResponse(BaseModel):
    """题目响应"""
    id: str
    content: str
    answer: str
    explanation: str
    knowledge_points: List[str]
    difficulty: str
    created_at: str
    subject: Optional[str] = "未分类"
    grade: Optional[str] = "未分类"

class ExportRequest(BaseModel):
    """导出请求"""
    question_ids: List[str]
    title: str = "练习题集"

# ==============================================================================
# 根端点
# ==============================================================================

@app.get("/")
def read_root():
    """根端点"""
    return {
        "message": "沐梧AI解题系统 - 数据库版本",
        "version": "V25.1",
        "features": {
            "user_auth": "JWT令牌认证",
            "database": "MySQL存储",
            "ai_solving": "AI解题功能",
            "mistake_book": "错题本管理",
            "question_generation": "智能出题",
            "pdf_export": "PDF导出（LaTeX支持）"
        },
        "auth_endpoints": {
            "register": "POST /auth/register",
            "login": "POST /auth/login",
            "verify": "GET /auth/verify",
            "me": "GET /auth/me"
        },
        "api_docs": "http://127.0.0.1:8000/docs"
    }

# ==============================================================================
# AI解题功能（保留原功能，添加认证）
# ==============================================================================

@app.post("/solve")
async def solve_question(
    image: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """
    AI解题功能（需要认证）
    
    上传图片，返回解题过程
    """
    # 读取图片
    image_bytes = await image.read()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    # 调用AI解题（保持原有逻辑）
    try:
        messages = [{
            'role': 'user',
            'content': [
                {'image': f'data:image/jpeg;base64,{image_base64}'},
                {'text': '请详细解答这道题目，包括解题思路、步骤和答案。'}
            ]
        }]
        
        response = dashscope.MultiModalConversation.call(
            model='qwen-vl-max',
            messages=messages
        )
        
        if response.status_code == 200:
            answer = response.output.choices[0].message.content[0]['text']
            return {
                "success": True,
                "answer": answer,
                "user_id": user["user_id"]
            }
        else:
            raise HTTPException(status_code=500, detail="AI解题失败")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat_with_image(
    image: Optional[UploadFile] = File(None),
    mode: str = Form("solve"),
    prompt: str = Form(...),
    solve_type: str = Form("single"),
    specific_question: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """
    统一的对话接口（需要认证）
    
    支持：
    - 解题模式 (mode=solve)
    - 批改作业模式 (mode=review)
    - 自动保存错题到数据库
    """
    user_id = user["user_id"]
    
    try:
        # 读取图片（如果有）
        image_base64 = None
        if image:
            image_bytes = await image.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # 构建AI请求
        if image_base64:
            messages = [{
                'role': 'user',
                'content': [
                    {'image': f'data:image/jpeg;base64,{image_base64}'},
                    {'text': prompt}
                ]
            }]
        else:
            messages = [{'role': 'user', 'content': prompt}]
        
        # 调用AI
        response = dashscope.MultiModalConversation.call(
            model='qwen-vl-max',
            messages=messages
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="AI调用失败")
        
        ai_response = response.output.choices[0].message.content[0]['text']
        
        # 如果是批改模式，检测是否有错题并自动保存
        mistake_saved = False
        knowledge_points = []
        
        if mode == 'review':
            # 检测是否是错题（简单判断：包含"错误"、"不正确"等关键词）
            is_mistake = any(keyword in ai_response for keyword in [
                '错误', '不正确', '不对', '有误', '答案错了', '做错了'
            ])
            
            if is_mistake and image_base64:
                # 提取知识点（使用AI二次提取）
                try:
                    extract_prompt = f"请从以下批改结果中提取涉及的知识点，以逗号分隔返回，不要其他内容：\n\n{ai_response}"
                    extract_response = dashscope.Generation.call(
                        model='qwen-turbo',
                        prompt=extract_prompt
                    )
                    
                    if extract_response.status_code == 200:
                        kp_text = extract_response.output.text.strip()
                        knowledge_points = [kp.strip() for kp in kp_text.split('，') if kp.strip()]
                        if not knowledge_points:
                            knowledge_points = [kp.strip() for kp in kp_text.split(',') if kp.strip()]
                    
                    if not knowledge_points:
                        knowledge_points = ['未分类']
                except:
                    knowledge_points = ['未分类']
                
                # 保存错题到数据库
                import uuid
                import json
                
                subject_id = str(uuid.uuid4())
                
                # 创建subject记录（使用with语句管理数据库连接）
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        
                        # 插入subject表
                        cursor.execute("""
                            INSERT INTO subject (
                                subject_id, subject_title, subject_desc, 
                                solve, answer, explanation,
                                subject_type, difficulty, knowledge_points,
                                subject_name, grade, created_at
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                            )
                        """, (
                            subject_id,
                            "批改发现的错题",  # subject_title
                            prompt[:200],  # subject_desc（截取prompt前200字）
                            "",  # solve
                            "",  # answer
                            ai_response,  # explanation（AI批改结果）
                            "mistake",  # subject_type
                            "中等",  # difficulty
                            json.dumps(knowledge_points, ensure_ascii=False),  # knowledge_points
                            knowledge_points[0] if knowledge_points else "未分类",  # subject_name
                            "未分类",  # grade
                        ))
                        
                        # 获取或创建用户的错题本试卷
                        cursor.execute("""
                            SELECT exam_id FROM exam 
                            WHERE exam_title LIKE %s AND exam_type = 'mistake'
                            LIMIT 1
                        """, (f"{user['account']}的错题本%",))
                        
                        exam_result = cursor.fetchone()
                        
                        if exam_result:
                            exam_id = exam_result['exam_id']
                        else:
                            # 创建新的错题本试卷
                            exam_id = str(uuid.uuid4())
                            cursor.execute("""
                                INSERT INTO exam (exam_id, exam_title, exam_content, exam_type, created_at)
                                VALUES (%s, %s, %s, 'mistake', NOW())
                            """, (
                                exam_id,
                                f"{user['account']}的错题本",
                                "自动保存的错题"
                            ))
                        
                        # 插入user_exam关联
                        cursor.execute("""
                            INSERT INTO user_exam (
                                id, user_info, subject_id, exam_id,
                                answered_at, user_answer, status
                            ) VALUES (
                                %s, %s, %s, %s, NOW(), %s, 'wrong'
                            )
                        """, (
                            str(uuid.uuid4()),
                            user_id,
                            subject_id,
                            exam_id,
                            "错误答案（批改发现）"
                        ))
                        
                        conn.commit()
                        mistake_saved = True
                        cursor.close()
                        
                except Exception as e:
                    print(f"[错题保存失败] {str(e)}")
                    import traceback
                    traceback.print_exc()
        
        return {
            "success": True,
            "response": ai_response,
            "mistake_saved": mistake_saved,
            "knowledge_points": knowledge_points,
            "user_id": user_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# 错题本API（数据库版本）
# ==============================================================================

@app.post("/mistakes/", response_model=MistakeResponse)
async def create_mistake(
    mistake: MistakeCreate,
    user: dict = Depends(get_current_user)
):
    """
    创建新错题（需要认证）
    
    自动保存到用户的错题本试卷中
    """
    user_id = user["user_id"]
    
    # 创建subject记录
    import json
    subject_id = SubjectManager.create_subject(
        subject_title=mistake.question_text,
        subject_desc="用户上传的错题",
        image_url=f"data:image/png;base64,{mistake.image_base64[:100]}...",
        solve=mistake.ai_analysis
    )
    
    # 更新subject的额外字段
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE subject SET 
               subject_type = %s,
               subject_name = %s,
               grade = %s,
               knowledge_points = %s,
               answer = %s,
               explanation = %s
               WHERE subject_id = %s""",
            (
                'mistake',
                mistake.subject,
                mistake.grade,
                json.dumps(mistake.knowledge_points, ensure_ascii=False),
                mistake.wrong_answer,
                mistake.ai_analysis,
                subject_id
            )
        )
        
        # 获取用户的错题本试卷ID
        cursor.execute(
            """SELECT exam_id FROM exam 
               WHERE exam_type = 'mistake_book' 
               AND exam_id IN (
                   SELECT DISTINCT exam_id FROM user_exam WHERE user_info = %s
               )
               LIMIT 1""",
            (user_id,)
        )
        
        exam_result = cursor.fetchone()
        if not exam_result:
            # 如果没有错题本，创建一个
            from database import ExamManager
            exam_id = ExamManager.create_exam(
                exam_title=f"{user['account']}的错题本",
                exam_content="记录所有错题"
            )
            cursor.execute(
                "UPDATE exam SET exam_type = %s WHERE exam_id = %s",
                ('mistake_book', exam_id)
            )
        else:
            exam_id = exam_result['exam_id']
        
        # 关联用户-试卷-题目
        ExamManager.link_user_exam_subject(user_id, exam_id, subject_id)
        
        # 获取创建时间
        cursor.execute(
            "SELECT created_at FROM subject WHERE subject_id = %s",
            (subject_id,)
        )
        created_at = cursor.fetchone()['created_at']
    
    return MistakeResponse(
        id=subject_id,
        image_base64=mistake.image_base64,
        question_text=mistake.question_text,
        wrong_answer=mistake.wrong_answer,
        ai_analysis=mistake.ai_analysis,
        subject=mistake.subject,
        grade=mistake.grade,
        knowledge_points=mistake.knowledge_points,
        created_at=created_at.isoformat() if created_at else datetime.now().isoformat(),
        reviewed_count=0
    )

@app.get("/mistakes/")
async def get_mistakes(
    subject: Optional[str] = None,
    grade: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user: dict = Depends(get_current_user)
):
    """
    获取错题列表（需要认证）
    
    只返回当前用户的错题
    """
    user_id = user["user_id"]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 构建查询
        query = """
            SELECT s.*, ue.answered_at, ue.user_answer, ue.status
            FROM subject s
            JOIN user_exam ue ON s.subject_id = ue.subject_id
            WHERE ue.user_info = %s AND s.subject_type = 'mistake'
        """
        params = [user_id]
        
        if subject:
            query += " AND s.subject_name = %s"
            params.append(subject)
        
        if grade:
            query += " AND s.grade = %s"
            params.append(grade)
        
        query += " ORDER BY s.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        mistakes = cursor.fetchall()
        
        # 【修复】格式化返回数据，包含完整图片和解析
        items = []
        import json
        for m in mistakes:
            # 【修复】提取完整的图片base64（移除data URI前缀）
            image_data = ""
            if m['image_url']:
                if m['image_url'].startswith('data:image'):
                    # 移除 "data:image/jpeg;base64," 前缀
                    image_data = m['image_url'].split(',', 1)[1] if ',' in m['image_url'] else m['image_url']
                else:
                    image_data = m['image_url']
            
            # 【调试】打印数据库原始字段
            print(f"\n[错题查询调试] 错题ID: {m['subject_id']}")
            print(f"  - subject_title: {m.get('subject_title', 'None')[:50] if m.get('subject_title') else 'None'}")
            print(f"  - subject_desc: {m.get('subject_desc', 'None')[:50] if m.get('subject_desc') else 'None'}")
            print(f"  - solve: {m.get('solve', 'None')[:50] if m.get('solve') else 'None'}")
            print(f"  - explanation: {m.get('explanation', 'None')[:50] if m.get('explanation') else 'None'}")
            print(f"  - answer: {m.get('answer', 'None')[:50] if m.get('answer') else 'None'}")
            print(f"  - image_url: {'有图片' if m.get('image_url') else '无图片'}")
            
            items.append({
                "id": m['subject_id'],
                "image_base64": image_data,  # 【修复】返回完整图片
                "question_text": m['subject_desc'] or m['subject_title'] or "错题",  # 【修复】使用题目描述
                "wrong_answer": m['answer'] or "",
                "ai_analysis": m['solve'] or m['explanation'] or "",  # 【修复】使用完整解析
                "subject": m['subject_name'] or "未分类",
                "grade": m['grade'] or "未分类",
                "knowledge_points": json.loads(m['knowledge_points']) if m['knowledge_points'] else [],
                "created_at": m['created_at'].isoformat() if m['created_at'] else "",
                "reviewed_count": 0  # TODO: 从user_exam表统计
            })
        
        return {
            "total": len(items),
            "items": items,
            "offset": offset,
            "limit": limit
        }

@app.delete("/mistakes/{mistake_id}")
async def delete_mistake(
    mistake_id: str,
    user: dict = Depends(get_current_user)
):
    """
    删除错题（需要认证）
    
    只能删除自己的错题
    """
    user_id = user["user_id"]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 验证权限
        cursor.execute(
            """SELECT COUNT(*) as count FROM user_exam 
               WHERE subject_id = %s AND user_info = %s""",
            (mistake_id, user_id)
        )
        
        if cursor.fetchone()['count'] == 0:
            raise HTTPException(status_code=404, detail="错题不存在或无权限删除")
        
        # 删除user_exam记录
        cursor.execute(
            "DELETE FROM user_exam WHERE subject_id = %s AND user_info = %s",
            (mistake_id, user_id)
        )
        
        # 删除subject记录（如果没有其他用户使用）
        cursor.execute(
            "SELECT COUNT(*) as count FROM user_exam WHERE subject_id = %s",
            (mistake_id,)
        )
        
        if cursor.fetchone()['count'] == 0:
            cursor.execute("DELETE FROM subject WHERE subject_id = %s", (mistake_id,))
    
    return {"success": True, "message": "删除成功"}

@app.get("/mistakes/stats/summary")
async def get_mistakes_stats(user: dict = Depends(get_current_user)):
    """
    获取错题统计信息（需要认证）
    """
    user_id = user["user_id"]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 统计总数
        cursor.execute(
            """SELECT COUNT(*) as total FROM user_exam 
               WHERE user_info = %s AND subject_id IN (
                   SELECT subject_id FROM subject WHERE subject_type = 'mistake'
               )""",
            (user_id,)
        )
        total = cursor.fetchone()['total']
        
        # 统计学科
        cursor.execute(
            """SELECT s.subject_name, COUNT(*) as count
               FROM subject s
               JOIN user_exam ue ON s.subject_id = ue.subject_id
               WHERE ue.user_info = %s AND s.subject_type = 'mistake'
               GROUP BY s.subject_name""",
            (user_id,)
        )
        subjects = {row['subject_name']: row['count'] for row in cursor.fetchall()}
        
        # 统计年级
        cursor.execute(
            """SELECT s.grade, COUNT(*) as count
               FROM subject s
               JOIN user_exam ue ON s.subject_id = ue.subject_id
               WHERE ue.user_info = %s AND s.subject_type = 'mistake'
               GROUP BY s.grade""",
            (user_id,)
        )
        grades = {row['grade']: row['count'] for row in cursor.fetchall()}
        
        # 知识点统计
        import json
        cursor.execute(
            """SELECT s.knowledge_points
               FROM subject s
               JOIN user_exam ue ON s.subject_id = ue.subject_id
               WHERE ue.user_info = %s AND s.subject_type = 'mistake'
               AND s.knowledge_points IS NOT NULL""",
            (user_id,)
        )
        
        kp_dict = {}
        for row in cursor.fetchall():
            if row['knowledge_points']:
                try:
                    kps = json.loads(row['knowledge_points'])
                    for kp in kps:
                        kp_dict[kp] = kp_dict.get(kp, 0) + 1
                except:
                    pass
        
        top_kps = sorted(kp_dict.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_mistakes": total,
            "subjects": subjects,
            "grades": grades,
            "top_knowledge_points": top_kps
        }

# ==============================================================================
# 【V25.1】网络辅助出题工具函数
# ==============================================================================

async def search_web_for_questions(subject: str, knowledge_points: List[str], difficulty: str) -> str:
    """
    【V25.1集成】网络深度爬取辅助出题功能
    
    策略：
    1. 搜索并识别题库网站
    2. 深度爬取题目详情页
    3. 提取题目文本和图片
    4. 返回结构化的真实题目数据
    """
    import requests
    from bs4 import BeautifulSoup
    import re
    from urllib.parse import urljoin
    
    kp_str = " ".join(knowledge_points[:2])
    search_query = f"{subject} {kp_str} {difficulty} 练习题 含图 site:jyeoo.com OR site:zujuan.com OR site:cooco.net.cn"
    
    print(f"[深度爬取] 搜索关键词: {search_query}")
    print(f"[深度爬取] 目标: 带图片的真实题目")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        # 步骤1: 搜索题库网站
        search_url = f"https://www.baidu.com/s?wd={requests.utils.quote(search_query)}"
        response = requests.get(search_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取题库网站链接
        question_urls = []
        target_sites = ['jyeoo.com', 'zujuan.com', 'cooco.net.cn', '1010jiajiao.com', 'zybang.com']
        
        for result in soup.find_all('div', class_=['result', 'c-container'], limit=20):
            mu_url = result.get('mu')
            if mu_url and any(site in mu_url for site in target_sites):
                question_urls.append(mu_url)
                continue
            
            data_log = result.get('data-log')
            if data_log:
                try:
                    url_match = re.search(r'http[s]?://[^\s"\']+', data_log)
                    if url_match:
                        extracted_url = url_match.group(0)
                        if any(site in extracted_url for site in target_sites):
                            question_urls.append(extracted_url)
                            continue
                except:
                    pass
            
            link = result.find('a', href=True)
            if link and link['href']:
                href = link['href']
                if 'baidu.com' in href and 'url=' in href:
                    try:
                        real_url_match = re.search(r'url=([^&]+)', href)
                        if real_url_match:
                            import urllib.parse
                            real_url = urllib.parse.unquote(real_url_match.group(1))
                            if any(site in real_url for site in target_sites):
                                question_urls.append(real_url)
                    except:
                        pass
        
        question_urls = list(set(question_urls))
        print(f"[深度爬取] ✓ 找到 {len(question_urls)} 个题库链接")
        
        # 如果没找到链接，尝试直接访问题库
        if len(question_urls) == 0:
            print(f"[深度爬取] ⚠️ 未找到链接，尝试直接访问...")
            jyeoo_keywords = f"{subject} {' '.join(knowledge_points[:2])}"
            jyeoo_search_url = f"https://www.jyeoo.com/search?q={requests.utils.quote(jyeoo_keywords)}&type=question"
            question_urls.append(jyeoo_search_url)
        
        # 步骤2: 爬取题目详情
        questions_data = []
        
        for url in question_urls[:3]:
            try:
                print(f"[深度爬取] 正在访问: {url[:50]}...")
                detail_response = requests.get(url, headers=headers, timeout=8)
                detail_response.encoding = 'utf-8'
                detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                
                question_text = ""
                possible_selectors = [
                    {'class': 'question'}, {'class': 'stem'},
                    {'class': 'timu'}, {'class': 'topic-title'},
                    {'id': 'question'}
                ]
                
                for selector in possible_selectors:
                    elem = detail_soup.find('div', selector)
                    if elem:
                        question_text = elem.get_text(strip=True)[:500]
                        break
                
                images = []
                img_tags = detail_soup.find_all('img', limit=5)
                for img in img_tags:
                    src = img.get('src') or img.get('data-src')
                    if src and ('question' in src.lower() or 'upload' in src.lower()):
                        absolute_url = urljoin(url, src)
                        images.append(absolute_url)
                
                if question_text or images:
                    questions_data.append({
                        'text': question_text,
                        'images': images,
                        'source': url
                    })
                    print(f"[深度爬取] ✓ 提取题目: {len(question_text)}字符, {len(images)}张图片")
                    
            except Exception as e:
                print(f"[深度爬取] ⚠️ 爬取失败: {str(e)[:50]}")
                continue
        
        # 步骤3: 格式化返回数据
        if questions_data:
            result_text = f"【网络爬取到 {len(questions_data)} 道真实题目】\n\n"
            
            for i, q in enumerate(questions_data, 1):
                result_text += f"题目{i}:\n"
                result_text += f"内容: {q['text'][:300]}\n"
                
                if q['images']:
                    result_text += f"包含图片: {len(q['images'])}张\n"
                    result_text += f"图片URL: {q['images'][0]}\n"
                    result_text += "【重要】此题包含精确图形，建议直接使用或轻微改编\n"
                
                result_text += f"来源: {q['source'][:80]}...\n---\n\n"
            
            result_text += """
【出题建议】
1. 对于包含复杂图形的题目：
   - 直接使用原题（修改数字或文字）
   - 保留图片URL或描述图片内容
   - 不要用SVG重绘复杂图形
   
2. 对于纯文字题目：
   - 可以自由改编
   - 适当增加图表辅助
"""
            
            print(f"[深度爬取] ✓ 成功爬取 {len(questions_data)} 道题目")
            return result_text
        else:
            print(f"[深度爬取] ⚠️ 未能爬取到题目，降级为摘要模式")
            return await _fallback_simple_search(subject, knowledge_points, difficulty, headers)
            
    except Exception as e:
        print(f"[深度爬取] ❌ 爬取失败: {e}")
        try:
            return await _fallback_simple_search(subject, knowledge_points, difficulty, headers)
        except:
            raise


async def _fallback_simple_search(subject: str, knowledge_points: List[str], difficulty: str, headers: dict) -> str:
    """
    【V25.1集成】降级策略：简单摘要搜索
    """
    import requests
    from bs4 import BeautifulSoup
    
    kp_str = " ".join(knowledge_points[:3])
    search_query = f"{subject} {kp_str} {difficulty} 练习题"
    search_url = f"https://www.baidu.com/s?wd={requests.utils.quote(search_query)}"
    
    print(f"[降级搜索] 搜索关键词: {search_query}")
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        result_texts = []
        for result in soup.find_all('div', class_=['result', 'c-container'], limit=10):
            title_elem = result.find(['h3', 'a'])
            if title_elem:
                title = title_elem.get_text(strip=True)
                if len(title) > 10:
                    result_texts.append(f"【题型参考】{title}")
            
            abstract_elem = result.find(['div', 'span'], class_=['c-abstract', 'content-right_8Zs40'])
            if abstract_elem:
                abstract = abstract_elem.get_text(strip=True)
                if len(abstract) > 20:
                    result_texts.append(f"内容: {abstract[:200]}")
            
            result_texts.append("---")
        
        combined_text = "\n".join(result_texts)
        if len(combined_text) > 3000:
            combined_text = combined_text[:3000] + "\n...(已截断)"
        
        print(f"[降级搜索] 提取到 {len(result_texts)//3} 条参考信息")
        
        if len(combined_text) < 200:
            combined_text += f"""

【出题指导】
主题：{subject} - {kp_str}
难度：{difficulty}

建议题型：
1. 概念理解题
2. 计算应用题
3. 综合分析题

注意：如需图形，使用简单SVG或文字描述
"""
        
        return combined_text if combined_text.strip() else "（网络搜索未返回结果）"
    
    except Exception as e:
        print(f"[降级搜索] ❌ 搜索失败: {e}")
        return f"""
【网络搜索不可用 - AI独立出题】
主题：{subject} - {' '.join(knowledge_points[:3])}
难度：{difficulty}

请根据主题和学生错题特点，生成高质量练习题。
"""

# ==============================================================================
# 题目生成API（数据库版本）
# ==============================================================================

@app.post("/questions/generate")
async def generate_questions(
    request: QuestionGenerateRequest,
    user: dict = Depends(get_current_user)
):
    """
    【V25.1完整版】基于错题生成新题目（需要认证）
    
    支持：
    - AI智能出题
    - 网络辅助出题（可选）
    - 自动保存到数据库
    """
    user_id = user["user_id"]
    
    # 获取用户的错题
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 查询指定的错题
        if not request.mistake_ids:
            raise HTTPException(status_code=400, detail="未指定错题")
        
        placeholders = ','.join(['%s'] * len(request.mistake_ids))
        query = f"""
            SELECT s.*, ue.user_answer
            FROM subject s
            JOIN user_exam ue ON s.subject_id = ue.subject_id
            WHERE ue.user_info = %s 
            AND s.subject_type = 'mistake'
            AND s.subject_id IN ({placeholders})
        """
        cursor.execute(query, [user_id] + request.mistake_ids)
        selected_mistakes = cursor.fetchall()
    
    if not selected_mistakes:
        raise HTTPException(status_code=400, detail="未找到指定的错题")
    
    # 提取知识点和学科信息
    import json
    all_knowledge_points = []
    subjects = set()
    
    for mistake in selected_mistakes:
        if mistake['knowledge_points']:
            try:
                kps = json.loads(mistake['knowledge_points'])
                all_knowledge_points.extend(kps)
            except:
                pass
        if mistake.get('subject_name'):
            subjects.add(mistake['subject_name'])
    
    knowledge_points_str = "、".join(set(all_knowledge_points)) if all_knowledge_points else "综合知识"
    subject_str = "、".join(subjects) if subjects else "综合"
    
    # 网络辅助出题
    web_reference_text = ""
    if request.allow_web_search:
        print(f"\n{'='*70}")
        print(f"[网络辅助出题] 启用网络搜索模式")
        print(f"{'='*70}\n")
        
        try:
            web_reference_text = await search_web_for_questions(
                subject=subject_str,
                knowledge_points=list(set(all_knowledge_points)),
                difficulty=request.difficulty
            )
            print(f"[网络辅助出题] ✓ 获取到参考资料，长度: {len(web_reference_text)} 字符")
        except Exception as e:
            print(f"[网络辅助出题] ⚠️ 网络搜索失败: {e}")
            web_reference_text = ""
    
    # 构建AI提示词
    mistakes_context = "\n\n".join([
        f"错题{i+1}：\n{m['subject_title'][:300]}\n学生答案：{m.get('user_answer', '未知')[:200]}"
        for i, m in enumerate(selected_mistakes[:5])
    ])
    
    if request.allow_web_search and web_reference_text:
        prompt = f"""请基于以下学生的错题情况和网络搜集的真实题目，生成{request.count}道{request.difficulty}难度的练习题。

【学生错题情况】
{mistakes_context}

【涉及知识点】{knowledge_points_str}

【网络搜集的真实题目参考】
{web_reference_text}

【重要要求】
1. 如果参考题目包含复杂图形，请：
   - 直接使用该题目并进行轻微改编（如修改数字、条件）
   - 在题目中注明"参考图片：[URL]"
   - 不要尝试用SVG重新绘制复杂图形（AI绘制不够精确）

2. 对于适合生成图形的题目：
   - 简单几何图形可以使用SVG代码
   - 表格数据使用Markdown表格语法
   - 复杂图形用详细文字描述

3. 题目格式要求：
   - 每道题包含：题目、答案、解析
   - 支持LaTeX数学公式（用$$包裹）
   - 难度为{request.difficulty}

请返回{request.count}道题目，格式如下：

题目1：
[题目内容，可包含SVG、Markdown表格、LaTeX公式]

答案：
[答案内容]

解析：
[详细解析]

知识点：[知识点1、知识点2]

---

题目2：
...
"""
    else:
        prompt = f"""请基于以下学生的错题情况，生成{request.count}道{request.difficulty}难度的练习题。

【学生错题情况】
{mistakes_context}

【涉及知识点】{knowledge_points_str}

【题目要求】
1. 针对学生的薄弱环节，设计有针对性的练习题
2. 难度为{request.difficulty}
3. 可以使用：
   - LaTeX数学公式（用$$包裹）
   - 简单SVG图形（避免过于复杂的图形）
   - Markdown表格

请返回{request.count}道题目，格式如下：

题目1：
[题目内容]

答案：
[答案内容]

解析：
[详细解析]

知识点：[知识点1、知识点2]

---

题目2：
...
"""
    
    # 调用AI生成题目
    try:
        messages = [{'role': 'user', 'content': prompt}]
        response = dashscope.Generation.call(
            model='qwen-max',
            messages=messages,
            result_format='message'
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="AI生成失败")
        
        generated_text = response.output.choices[0].message.content
        
        # 解析生成的题目并保存到数据库
        # 简化版：将整体文本作为题目保存
        # TODO: 可以添加更精细的解析逻辑
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 创建练习题集试卷（如果不存在）
            cursor.execute(
                """SELECT exam_id FROM exam 
                   WHERE exam_type = 'practice_set'
                   AND exam_id IN (
                       SELECT DISTINCT exam_id FROM user_exam WHERE user_info = %s
                   )
                   LIMIT 1""",
                (user_id,)
            )
            
            exam_result = cursor.fetchone()
            if not exam_result:
                exam_id = ExamManager.create_exam(
                    exam_title=f"{user['account']}的练习题集",
                    exam_content="AI生成的练习题"
                )
                cursor.execute(
                    "UPDATE exam SET exam_type = %s WHERE exam_id = %s",
                    ('practice_set', exam_id)
                )
            else:
                exam_id = exam_result['exam_id']
            
            # 保存生成的题目
            subject_id = SubjectManager.create_subject(
                subject_title=generated_text,
                subject_desc=f"基于错题生成的{request.difficulty}难度练习题",
                solve=generated_text
            )
            
            cursor.execute(
                """UPDATE subject SET 
                   subject_type = %s,
                   subject_name = %s,
                   difficulty = %s,
                   knowledge_points = %s
                   WHERE subject_id = %s""",
                (
                    'generated',
                    subject_str,
                    request.difficulty,
                    json.dumps(list(set(all_knowledge_points)), ensure_ascii=False),
                    subject_id
                )
            )
            
            # 关联用户-试卷-题目
            ExamManager.link_user_exam_subject(user_id, exam_id, subject_id)
        
        return {
            "success": True,
            "message": f"成功生成{request.count}道题目",
            "content": generated_text,
            "subject_id": subject_id,
            "user_id": user_id
        }
    
    except Exception as e:
        print(f"[题目生成] ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"题目生成失败: {str(e)}")

@app.get("/questions/")
async def get_questions(
    subject: Optional[str] = None,
    grade: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user: dict = Depends(get_current_user)
):
    """
    获取生成的题目列表（需要认证）
    """
    user_id = user["user_id"]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT s.*
            FROM subject s
            JOIN user_exam ue ON s.subject_id = ue.subject_id
            WHERE ue.user_info = %s AND s.subject_type = 'generated'
        """
        params = [user_id]
        
        if subject:
            query += " AND s.subject_name = %s"
            params.append(subject)
        
        if grade:
            query += " AND s.grade = %s"
            params.append(grade)
        
        query += " ORDER BY s.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        questions = cursor.fetchall()
        
        import json
        items = []
        for q in questions:
            # 题目内容优先使用 solve（完整内容），其次 subject_desc，最后才是 subject_title
            content = q['solve'] or q['subject_desc'] or q['subject_title'] or ""
            
            items.append({
                "id": q['subject_id'],
                "content": content,  # 使用完整题目内容
                "answer": q['answer'] or "",
                "explanation": q['explanation'] or "",
                "knowledge_points": json.loads(q['knowledge_points']) if q['knowledge_points'] else [],
                "difficulty": q['difficulty'] or "中等",
                "created_at": q['created_at'].isoformat() if q['created_at'] else "",
                "subject": q['subject_name'] or "未分类",
                "grade": q['grade'] or "未分类",
                "title": q['subject_title'] or ""  # 添加标题字段
            })
        
        return {
            "total": len(items),
            "items": items,
            "offset": offset,
            "limit": limit
        }

@app.delete("/questions/{question_id}")
async def delete_question(
    question_id: str,
    user: dict = Depends(get_current_user)
):
    """删除题目（需要认证）"""
    user_id = user["user_id"]
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 验证权限
        cursor.execute(
            """SELECT COUNT(*) as count FROM user_exam 
               WHERE subject_id = %s AND user_info = %s""",
            (question_id, user_id)
        )
        
        if cursor.fetchone()['count'] == 0:
            raise HTTPException(status_code=404, detail="题目不存在或无权限删除")
        
        # 删除
        cursor.execute(
            "DELETE FROM user_exam WHERE subject_id = %s AND user_info = %s",
            (question_id, user_id)
        )
        
        cursor.execute(
            "SELECT COUNT(*) as count FROM user_exam WHERE subject_id = %s",
            (question_id,)
        )
        
        if cursor.fetchone()['count'] == 0:
            cursor.execute("DELETE FROM subject WHERE subject_id = %s", (question_id,))
    
    return {"success": True, "message": "删除成功"}

# ==============================================================================
# 【V25.1】PDF导出功能
# ==============================================================================

@app.post("/export/pdf")
async def export_pdf(
    request: ExportRequest,
    user: dict = Depends(get_current_user)
):
    """
    【V25.1完整版】导出为PDF格式（需要认证）
    
    技术方案：
    1. 将题目的Markdown内容转换为HTML
    2. 在HTML中注入MathJax配置和CDN
    3. 使用Pyppeteer（无头浏览器）加载HTML并执行MathJax渲染
    4. 将渲染后的页面打印为PDF
    
    这确保了LaTeX公式能够正确显示在PDF中
    """
    from pyppeteer import launch
    import markdown
    
    user_id = user["user_id"]
    
    # 获取用户的题目
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        placeholders = ','.join(['%s'] * len(request.question_ids))
        query = f"""
            SELECT s.*
            FROM subject s
            JOIN user_exam ue ON s.subject_id = ue.subject_id
            WHERE ue.user_info = %s
            AND s.subject_id IN ({placeholders})
        """
        cursor.execute(query, [user_id] + request.question_ids)
        selected = cursor.fetchall()
    
    if not selected:
        raise HTTPException(status_code=400, detail="未找到指定的题目")
    
    print(f"\n{'='*70}")
    print(f"[PDF导出] 准备导出{len(selected)}道题目")
    print(f"{'='*70}\n")
    
    try:
        # 步骤1: 构建包含MathJax的HTML
        print("[PDF导出] 步骤1: 构建HTML文档...")
        
        html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>练习题集</title>
    
    <!-- MathJax 3配置 -->
    <script>
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$']],
                displayMath: [['$$', '$$']],
                processEscapes: true,
                processEnvironments: true
            },
            svg: {
                fontCache: 'global',
                displayAlign: 'left'
            },
            startup: {
                pageReady: () => {
                    return MathJax.startup.defaultPageReady().then(() => {
                        console.log('✅ MathJax渲染完成');
                        document.body.setAttribute('data-mathjax-ready', 'true');
                    }).catch((err) => {
                        console.error('❌ MathJax渲染失败:', err);
                        document.body.setAttribute('data-mathjax-ready', 'error');
                    });
                }
            },
            options: {
                enableMenu: false,
                renderActions: { addMenu: [] }
            }
        };
    </script>
    <script id="MathJax-script" src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
    
    <!-- 样式 -->
    <style>
        body {
            font-family: "SimSun", "Microsoft YaHei", sans-serif;
            line-height: 1.8;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            color: #333;
        }
        h1 {
            text-align: center;
            color: #5C6AC4;
            border-bottom: 3px solid #5C6AC4;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }
        .question {
            margin-bottom: 40px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 10px;
            border-left: 4px solid #5C6AC4;
        }
        .question-title {
            font-size: 18px;
            font-weight: bold;
            color: #5C6AC4;
            margin-bottom: 15px;
        }
        .question-content {
            margin-bottom: 15px;
            font-size: 14px;
            white-space: pre-wrap;
        }
        .answer {
            background: #e8f5e9;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .explanation {
            background: #fff3e0;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        .knowledge-points {
            margin-top: 10px;
            font-size: 12px;
        }
        .knowledge-point {
            display: inline-block;
            background: #e3f2fd;
            padding: 4px 10px;
            border-radius: 4px;
            margin-right: 8px;
            margin-top: 5px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        table td, table th {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        table th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
    </style>
</head>
<body>
"""
        
        # 添加标题
        html_content += f"""
    <h1>{request.title}</h1>
    <p style="text-align: center; color: #999; margin-bottom: 40px;">
        生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
    </p>
"""
        
        # 步骤2: 添加每道题目
        print(f"[PDF导出] 步骤2: 转换{len(selected)}道题目为HTML...")
        
        import json
        for i, q in enumerate(selected, 1):
            content_html = markdown.markdown(q['subject_title'] or '', extensions=['extra', 'nl2br'])
            answer_html = markdown.markdown(q.get('answer') or q.get('solve') or '')
            explanation_html = markdown.markdown(q.get('explanation') or '')
            
            html_content += f"""
    <div class="question">
        <div class="question-title">题目 {i}</div>
        <div class="question-content">{content_html}</div>
        
        <div class="answer">
            <strong style="color: #4CAF50;">答案：</strong>
            {answer_html}
        </div>
"""
            
            if explanation_html:
                html_content += f"""
        <div class="explanation">
            <strong style="color: #FF9800;">解析：</strong>
            {explanation_html}
        </div>
"""
            
            # 知识点
            if q.get('knowledge_points'):
                try:
                    kps = json.loads(q['knowledge_points'])
                    kp_tags = ''.join([f'<span class="knowledge-point">{kp}</span>' for kp in kps])
                    html_content += f"""
        <div class="knowledge-points">
            <strong>知识点：</strong>{kp_tags}
        </div>
"""
                except:
                    pass
            
            html_content += "    </div>\n"
        
        # HTML尾部
        html_content += """
    <script>
        if (window.MathJax) {
            MathJax.startup.promise.then(() => {
                document.body.setAttribute('data-mathjax-ready', 'true');
            });
        }
    </script>
</body>
</html>
"""
        
        print(f"[PDF导出] ✓ HTML文档构建完成, 大小: {len(html_content)} 字符")
        
        # 步骤3: 保存临时HTML文件
        temp_html = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.html')
        temp_html.write(html_content)
        temp_html_path = temp_html.name
        temp_html.close()
        
        print(f"[PDF导出] ✓ HTML文件保存至: {temp_html_path}")
        
        # 调试功能：保存HTML到固定位置
        try:
            debug_dir = Path(__file__).parent / "generated_papers"
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_html_path = debug_dir / "latest_export_debug.html"
            
            with open(debug_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"[PDF导出] 📝 调试HTML已保存至: {debug_html_path}")
        except Exception as debug_err:
            print(f"[PDF导出] ⚠️ 调试HTML保存失败: {debug_err}")
        
        # 步骤4: 使用Pyppeteer启动无头浏览器
        print("[PDF导出] 步骤3: 启动无头浏览器...")
        
        browser = await launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = await browser.newPage()
        
        print("[PDF导出] ✓ 浏览器启动成功")
        print(f"[PDF导出] 步骤4: 加载HTML并执行MathJax渲染...")
        
        # 计算超时时间：每道题2分钟
        question_count = len(selected)
        timeout_per_question = 120000  # 2分钟
        total_timeout = question_count * timeout_per_question
        print(f"[PDF导出] 题目数量: {question_count}道, 超时时间: {total_timeout/1000}秒")
        
        # 加载HTML文件
        await page.goto(f'file://{temp_html_path}', {
            'waitUntil': 'networkidle0',
            'timeout': total_timeout
        })
        
        # 等待MathJax渲染完成
        print("[PDF导出] 等待MathJax渲染...")
        mathjax_ready = False
        
        try:
            await page.waitForSelector('body[data-mathjax-ready="true"]', {'timeout': total_timeout})
            mathjax_ready = True
            print("[PDF导出] ✓ MathJax渲染完成")
        except Exception as e:
            print(f"[PDF导出] ⚠️ 标记检测超时，尝试手动等待...")
            
            try:
                await asyncio.sleep(5)
                has_mathjax = await page.evaluate('''() => {
                    const mjElements = document.querySelectorAll('.MathJax, .mjx-chtml, mjx-container');
                    return mjElements.length > 0;
                }''')
                
                if has_mathjax:
                    mathjax_ready = True
                    print(f"[PDF导出] ✓ MathJax渲染完成（检测到渲染元素）")
                else:
                    print(f"[PDF导出] ⚠️ 未检测到MathJax元素")
            except Exception as e2:
                print(f"[PDF导出] ⚠️ 手动检测失败: {e2}")
        
        if not mathjax_ready:
            print("[PDF导出] ⚠️ MathJax可能未完全渲染，但继续生成PDF")
        
        # 步骤5: 生成PDF
        print("[PDF导出] 步骤5: 生成PDF文件...")
        
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_pdf_path = temp_pdf.name
        temp_pdf.close()
        
        await page.pdf({
            'path': temp_pdf_path,
            'format': 'A4',
            'margin': {
                'top': '20mm',
                'bottom': '20mm',
                'left': '15mm',
                'right': '15mm'
            },
            'printBackground': True
        })
        
        print(f"[PDF导出] ✓ PDF生成成功: {temp_pdf_path}")
        
        # 关闭浏览器
        await browser.close()
        
        # 清理临时HTML文件
        os.remove(temp_html_path)
        
        print(f"{'='*70}")
        print(f"[PDF导出] ✅ 导出完成")
        print(f"{'='*70}\n")
        
        # 返回PDF文件
        return FileResponse(
            temp_pdf_path,
            media_type='application/pdf',
            filename=f"{request.title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            background=None
        )
        
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"[PDF导出] ❌ 导出失败")
        print(f"[PDF导出] 错误: {e}")
        print(f"{'='*70}\n")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")

# ==============================================================================
# 数据库版本：聊天API + 会话管理
# ==============================================================================

# 内存会话存储（简化版，生产环境应使用Redis）
chat_sessions = {}

class ChatRequest(BaseModel):
    """聊天请求"""
    session_id: Optional[str] = None
    prompt: str
    image_base64: Optional[str] = None
    mode: str = "solve"  # solve 或 review

class SessionInfo(BaseModel):
    """会话信息"""
    sessionId: str
    title: str
    timestamp: int
    mode: str
    imageSrc: Optional[str] = None
    messages: Optional[List[dict]] = []

@app.post("/api/db/chat")
async def db_chat(request: ChatRequest, user: dict = Depends(get_current_user)):
    """
    数据库版本的聊天API（支持JSON请求体 + 会话管理）
    """
    user_id = user["user_id"]
    
    try:
        # 获取或创建会话
        session_id = request.session_id
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            chat_sessions[session_id] = {
                "user_id": user_id,
                "messages": [],
                "image_base64": None,  # 【修复】保存会话图片
                "title": "新对话",
                "mode": request.mode,
                "created_at": datetime.now(timezone.utc)
            }
        
        # 验证会话所有权
        if session_id in chat_sessions and chat_sessions[session_id]["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="无权访问此会话")
        
        session = chat_sessions[session_id]
        
        # 【修复】如果是第一次发送图片，保存到会话中
        if request.image_base64:
            session["image_base64"] = request.image_base64
            print(f"[会话 {session_id}] 保存图片到会话，长度: {len(request.image_base64)}")
        
        # 【修复】构建AI请求 - 追问时使用会话中的图片
        current_image = request.image_base64 or session.get("image_base64")
        
        if current_image:
            # 有图片：发送图片+文本
            messages = session.get("messages", []).copy()
            messages.append({
                'role': 'user',
                'content': [
                    {'image': f'data:image/jpeg;base64,{current_image}'},
                    {'text': request.prompt}
                ]
            })
            print(f"[会话 {session_id}] 发送消息（带图片）: {request.prompt[:50]}...")
        else:
            # 无图片：只发送文本
            messages = session.get("messages", []).copy()
            messages.append({
                'role': 'user',
                'content': request.prompt
            })
            print(f"[会话 {session_id}] 发送消息（纯文本）: {request.prompt[:50]}...")
        
        # 调用AI
        response = dashscope.MultiModalConversation.call(
            model='qwen-vl-max',
            messages=messages
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="AI调用失败")
        
        ai_response = response.output.choices[0].message.content[0]['text']
        
        # 【优化】如果是批改模式，检测是否有错题并自动保存
        mistake_saved = False
        knowledge_points = []
        
        if request.mode == 'review':
            is_mistake = any(keyword in ai_response for keyword in [
                '错误', '不正确', '不对', '有误', '答案错了', '做错了', '有问题', '错了'
            ])
            
            print(f"\n{'='*60}")
            print(f"[错题检测] 是否检测到错误: {is_mistake}")
            print(f"[错题检测] 是否有图片: {bool(current_image)}")
            print(f"{'='*60}\n")
            
            # 使用 current_image 而不是 request.image_base64，支持追问时也能保存错题
            if is_mistake and current_image:
                try:
                    print("[知识点提取] 开始提取知识点...")
                    extract_prompt = f"请从以下批改结果中提取涉及的知识点，以逗号分隔返回，不要其他内容：\n\n{ai_response}"
                    extract_response = dashscope.Generation.call(
                        model='qwen-turbo',
                        prompt=extract_prompt
                    )
                    
                    if extract_response.status_code == 200:
                        kp_text = extract_response.output.text.strip()
                        print(f"[知识点提取] 原始结果: {kp_text}")
                        knowledge_points = [kp.strip() for kp in kp_text.split('，') if kp.strip()]
                        if not knowledge_points:
                            knowledge_points = [kp.strip() for kp in kp_text.split(',') if kp.strip()]
                        print(f"[知识点提取] 提取成功: {knowledge_points}")
                    
                    if not knowledge_points:
                        knowledge_points = ['未分类']
                        print("[知识点提取] 使用默认值: ['未分类']")
                except Exception as kp_error:
                    print(f"[知识点提取] 提取失败: {kp_error}")
                    knowledge_points = ['未分类']
                
                # 保存错题到数据库
                import uuid
                import json
                
                subject_id = str(uuid.uuid4())
                
                print(f"\n{'='*60}")
                print(f"[错题保存] 开始保存错题到数据库...")
                print(f"[错题保存] subject_id: {subject_id}")
                print(f"[错题保存] 知识点: {knowledge_points}")
                print(f"[错题保存] 用户ID: {user_id}")
                print(f"[错题保存] 图片长度: {len(current_image) if current_image else 0}")
                print(f"{'='*60}\n")
                
                # 【修复】提取题目信息和解析
                # 从AI响应中分离出题目描述和解析
                mistake_title = f"批改于 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                question_desc = request.prompt[:500] if request.prompt else "上传的作业题目"
                
                # 保存完整的AI解析（不截断）
                full_explanation = ai_response
                
                # 构建图片URL（使用data URI格式）
                image_url = f"data:image/jpeg;base64,{current_image}" if current_image else None
                
                print(f"[错题保存] 题目标题: {mistake_title}")
                print(f"[错题保存] 题目描述长度: {len(question_desc)}")
                print(f"[错题保存] 解析长度: {len(full_explanation)}")
                
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        
                        # 【修复】插入subject表，包含完整信息
                        print("[错题保存] 步骤1: 插入subject表（包含题目图片和完整解析）...")
                        cursor.execute("""
                            INSERT INTO subject (
                                subject_id, subject_title, subject_desc, 
                                image_url, solve, explanation,
                                subject_type, difficulty, knowledge_points,
                                subject_name, grade, created_at
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                            )
                        """, (
                            subject_id,
                            mistake_title,  # 【修复】使用时间戳作为标题
                            question_desc,  # 【修复】保存题目描述（用户提问或图片说明）
                            image_url,  # 【修复】保存题目图片
                            full_explanation,  # 【修复】保存完整的AI批改结果
                            full_explanation,  # explanation字段也保存完整解析
                            "mistake",
                            "中等",
                            json.dumps(knowledge_points, ensure_ascii=False),
                            knowledge_points[0] if knowledge_points else "未分类",
                            "未分类",
                        ))
                        print("[错题保存] ✅ subject表插入成功（已保存题目图片和完整解析）")
                        
                        # 获取或创建用户的错题本试卷
                        print("[错题保存] 步骤2: 获取或创建错题本...")
                        cursor.execute("""
                            SELECT exam_id FROM exam 
                            WHERE exam_title LIKE %s AND exam_type = 'mistake'
                            LIMIT 1
                        """, (f"{user['account']}的错题本%",))
                        
                        exam_result = cursor.fetchone()
                        
                        if exam_result:
                            exam_id = exam_result['exam_id']
                            print(f"[错题保存] ✅ 找到现有错题本: {exam_id}")
                        else:
                            exam_id = str(uuid.uuid4())
                            cursor.execute("""
                                INSERT INTO exam (exam_id, exam_title, exam_content, exam_type, created_at)
                                VALUES (%s, %s, %s, 'mistake', NOW())
                            """, (
                                exam_id,
                                f"{user['account']}的错题本",
                                "自动保存的错题"
                            ))
                            print(f"[错题保存] ✅ 创建新错题本: {exam_id}")
                        
                        # 插入user_exam关联
                        print("[错题保存] 步骤3: 插入user_exam关联...")
                        cursor.execute("""
                            INSERT INTO user_exam (
                                id, user_info, subject_id, exam_id,
                                answered_at, user_answer, status
                            ) VALUES (
                                %s, %s, %s, %s, NOW(), %s, 'wrong'
                            )
                        """, (
                            str(uuid.uuid4()),
                            user_id,
                            subject_id,
                            exam_id,
                            "错误答案（批改发现）"
                        ))
                        print("[错题保存] ✅ user_exam关联插入成功")
                        
                        conn.commit()
                        mistake_saved = True
                        print(f"\n{'='*60}")
                        print(f"[错题保存] ✅✅✅ 错题保存成功！")
                        print(f"[错题保存] subject_id: {subject_id}")
                        print(f"[错题保存] exam_id: {exam_id}")
                        print(f"[错题保存] 知识点: {', '.join(knowledge_points)}")
                        print(f"{'='*60}\n")
                        cursor.close()
                        
                except Exception as e:
                    print(f"\n{'='*60}")
                    print(f"[错题保存] ❌❌❌ 保存失败！")
                    print(f"[错题保存] 错误: {str(e)}")
                    print(f"{'='*60}\n")
                    import traceback
                    traceback.print_exc()
        
        # 【修复】保存对话历史到会话
        session["messages"].append({
            'role': 'user',
            'content': [
                {'image': f'data:image/jpeg;base64,{current_image}'},
                {'text': request.prompt}
            ] if current_image else request.prompt
        })
        session["messages"].append({
            'role': 'assistant',
            'content': ai_response
        })
        print(f"[会话 {session_id}] 保存对话历史，总消息数: {len(session['messages'])}")
        
        # 生成会话标题（首次请求时）
        title = chat_sessions[session_id]["title"]
        if not request.session_id and len(request.prompt) > 5:
            title = request.prompt[:20] + ("..." if len(request.prompt) > 20 else "")
            chat_sessions[session_id]["title"] = title
        
        return {
            "success": True,
            "response": ai_response,
            "session_id": session_id,
            "title": title,
            "mistake_saved": mistake_saved,
            "knowledge_points": knowledge_points
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/db/sessions")
async def get_sessions(mode: str, user: dict = Depends(get_current_user)):
    """获取用户的会话列表"""
    user_id = user["user_id"]
    
    # 从内存中筛选用户的会话（简化版）
    user_sessions = []
    for sid, sess in chat_sessions.items():
        if sess["user_id"] == user_id and sess.get("mode") == mode:
            user_sessions.append({
                "sessionId": sid,
                "title": sess.get("title", "新对话"),
                "timestamp": int(sess.get("created_at", datetime.now(timezone.utc)).timestamp() * 1000),
                "mode": sess.get("mode", "solve"),
                "imageSrc": sess.get("imageSrc"),
                "messages": sess.get("messages", [])
            })
    
    # 按时间倒序
    user_sessions.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {"sessions": user_sessions[:50]}  # 只返回最近50个


@app.post("/api/db/sessions")
async def save_session(session: SessionInfo, user: dict = Depends(get_current_user)):
    """保存会话到内存（简化版）"""
    user_id = user["user_id"]
    
    chat_sessions[session.sessionId] = {
        "user_id": user_id,
        "title": session.title,
        "mode": session.mode,
        "imageSrc": session.imageSrc,
        "messages": session.messages or [],
        "created_at": datetime.fromtimestamp(session.timestamp / 1000, tz=timezone.utc)
    }
    
    return {"success": True}


@app.delete("/api/db/sessions/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(get_current_user)):
    """删除会话"""
    user_id = user["user_id"]
    
    if session_id in chat_sessions:
        if chat_sessions[session_id]["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="无权删除此会话")
        
        del chat_sessions[session_id]
    
    return {"success": True}


# ==============================================================================
# V25.2 新增功能API
# ==============================================================================

# ---------------------------
# 1. 对话历史管理API
# ---------------------------

class ChatSessionCreate(BaseModel):
    """创建对话会话请求"""
    title: Optional[str] = "新对话"
    mode: str = "solve"
    subject: Optional[str] = "未分类"
    grade: Optional[str] = "未分类"

class ChatMessageCreate(BaseModel):
    """添加对话消息请求"""
    session_id: str
    role: str  # user / assistant
    content: str
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    message_type: str = "text"

class ChatRequestV2(BaseModel):
    """V25.2连续对话请求"""
    session_id: Optional[str] = None
    prompt: str
    image_base64: Optional[str] = None
    mode: str = "solve"
    subject: Optional[str] = "未分类"
    grade: Optional[str] = "未分类"


@app.post("/api/v2/chat/session/create")
async def create_chat_session(
    request: ChatSessionCreate,
    user: dict = Depends(get_current_user)
):
    """创建新的对话会话"""
    user_id = user["user_id"]
    
    try:
        session_id = ChatManager.create_session(
            user_id=user_id,
            title=request.title,
            mode=request.mode,
            subject=request.subject,
            grade=request.grade
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "会话创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {str(e)}")


@app.get("/api/v2/chat/sessions")
async def get_user_chat_sessions(
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """获取用户的所有对话会话"""
    user_id = user["user_id"]
    
    try:
        sessions = ChatManager.get_user_sessions(user_id, limit)
        return {
            "success": True,
            "sessions": sessions,
            "total": len(sessions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@app.get("/api/v2/chat/session/{session_id}/history")
async def get_chat_history(
    session_id: str,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """获取对话历史"""
    try:
        # 验证会话所有权
        session_info = ChatManager.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        if session_info['user_id'] != user["user_id"]:
            raise HTTPException(status_code=403, detail="无权访问此会话")
        
        history = ChatManager.get_session_history(session_id, limit)
        return {
            "success": True,
            "session_id": session_id,
            "history": history,
            "total": len(history)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史失败: {str(e)}")


@app.post("/api/v2/chat")
async def chat_with_history(
    request: ChatRequestV2,
    user: dict = Depends(get_current_user)
):
    """
    V25.2 连续对话API（支持历史记录）
    
    特性：
    - 自动保存对话历史到数据库
    - 支持多轮对话
    - 支持图文混合输入
    - 自动识别错题并保存
    """
    user_id = user["user_id"]
    
    try:
        # 1. 获取或创建会话
        session_id = request.session_id
        if not session_id:
            # 创建新会话
            session_id = ChatManager.create_session(
                user_id=user_id,
                title="新对话",
                mode=request.mode,
                subject=request.subject,
                grade=request.grade
            )
        else:
            # 验证会话所有权
            session_info = ChatManager.get_session_info(session_id)
            if not session_info or session_info['user_id'] != user_id:
                raise HTTPException(status_code=403, detail="无权访问此会话")
        
        # 2. 获取历史消息（用于上下文）
        history = ChatManager.get_session_history(session_id, limit=10)
        
        # 3. 构建AI消息（包含历史上下文）
        messages = []
        
        # 添加历史消息
        for msg in history:
            if msg['role'] == 'user':
                if msg['message_type'] == 'image' and msg.get('image_url'):
                    messages.append({
                        'role': 'user',
                        'content': [
                            {'text': msg['content']},
                            {'image': msg['image_url']}
                        ]
                    })
                else:
                    messages.append({
                        'role': 'user',
                        'content': msg['content']
                    })
            elif msg['role'] == 'assistant':
                messages.append({
                    'role': 'assistant',
                    'content': msg['content']
                })
        
        # 添加当前消息
        if request.image_base64:
            current_message_content = [
                {'text': request.prompt},
                {'image': f'data:image/jpeg;base64,{request.image_base64}'}
            ]
            message_type = "mixed"
        else:
            current_message_content = request.prompt
            message_type = "text"
        
        messages.append({
            'role': 'user',
            'content': current_message_content
        })
        
        # 4. 调用AI
        response = dashscope.MultiModalConversation.call(
            model='qwen-vl-max',
            messages=messages
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="AI调用失败")
        
        ai_response = response.output.choices[0].message.content[0]['text']
        
        # 5. 保存对话历史
        # 保存用户消息
        ChatManager.add_message(
            session_id=session_id,
            role='user',
            content=request.prompt,
            image_url=f'data:image/jpeg;base64,{request.image_base64[:100]}...' if request.image_base64 else None,
            message_type=message_type
        )
        
        # 保存AI回复
        ChatManager.add_message(
            session_id=session_id,
            role='assistant',
            content=ai_response,
            message_type='text'
        )
        
        # 6. 如果是批改模式，检测错题并自动保存
        mistake_saved = False
        mistake_id = None
        
        if request.mode == 'review' and request.image_base64:
            # 简单检测是否有错误
            if any(keyword in ai_response.lower() for keyword in ['错误', '不正确', '有误', 'wrong', 'incorrect']):
                # 提取知识点（简化版）
                knowledge_points = []
                if '知识点' in ai_response:
                    # 这里可以用更复杂的解析逻辑
                    knowledge_points = ["待分析"]
                
                # 保存错题
                try:
                    mistake_id = MistakeManager.save_mistake(
                        user_id=user_id,
                        subject_title=f"错题_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        subject_desc=request.prompt[:500],
                        image_url=None,  # 可以后续保存到文件系统
                        user_mistake_text="批改中发现的错误",
                        correct_answer="见解析",
                        explanation=ai_response,
                        knowledge_points=knowledge_points if knowledge_points else ["综合"],
                        subject_name=request.subject,
                        grade=request.grade,
                        difficulty="中等",
                        mistake_analysis=ai_response
                    )
                    mistake_saved = True
                except Exception as e:
                    print(f"⚠️ 保存错题失败: {e}")
        
        # 7. 自动更新会话标题（基于第一条消息）
        if len(history) == 0:
            # 第一条消息，自动生成标题
            title = request.prompt[:20] + "..." if len(request.prompt) > 20 else request.prompt
            ChatManager.update_session_title(session_id, title)
        
        return {
            "success": True,
            "session_id": session_id,
            "answer": ai_response,
            "mistake_saved": mistake_saved,
            "mistake_id": mistake_id,
            "message_count": len(history) + 2  # 历史 + 用户消息 + AI回复
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 对话处理失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"对话处理失败: {str(e)}")


@app.delete("/api/v2/chat/session/{session_id}")
async def delete_chat_session(
    session_id: str,
    user: dict = Depends(get_current_user)
):
    """删除对话会话"""
    try:
        # 验证会话所有权
        session_info = ChatManager.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        if session_info['user_id'] != user["user_id"]:
            raise HTTPException(status_code=403, detail="无权删除此会话")
        
        # 软删除
        success = ChatManager.delete_session(session_id, soft_delete=True)
        
        return {
            "success": success,
            "message": "会话已删除"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


# ---------------------------
# 2. 错题本增强API
# ---------------------------

class MistakeSaveRequest(BaseModel):
    """保存错题请求"""
    subject_title: str
    subject_desc: str
    image_base64: Optional[str] = None
    user_mistake_text: Optional[str] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    knowledge_points: Optional[List[str]] = None
    subject_name: str = "未分类"
    grade: str = "未分类"
    difficulty: str = "中等"


@app.post("/api/v2/mistakes/save")
async def save_mistake_manual(
    request: MistakeSaveRequest,
    user: dict = Depends(get_current_user)
):
    """手动保存错题"""
    user_id = user["user_id"]
    
    try:
        # 如果有图片，可以保存到文件系统（这里暂时跳过）
        image_url = None
        
        subject_id = MistakeManager.save_mistake(
            user_id=user_id,
            subject_title=request.subject_title,
            subject_desc=request.subject_desc,
            image_url=image_url,
            user_mistake_text=request.user_mistake_text,
            correct_answer=request.correct_answer,
            explanation=request.explanation,
            knowledge_points=request.knowledge_points,
            subject_name=request.subject_name,
            grade=request.grade,
            difficulty=request.difficulty
        )
        
        return {
            "success": True,
            "subject_id": subject_id,
            "message": "错题保存成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存错题失败: {str(e)}")


@app.get("/api/v2/mistakes")
async def get_user_mistakes(
    subject_name: Optional[str] = None,
    grade: Optional[str] = None,
    knowledge_point: Optional[str] = None,
    limit: int = 100,
    user: dict = Depends(get_current_user)
):
    """获取用户错题列表（支持筛选）"""
    user_id = user["user_id"]
    
    try:
        mistakes = MistakeManager.get_user_mistakes(
            user_id=user_id,
            subject_name=subject_name,
            grade=grade,
            knowledge_point=knowledge_point,
            limit=limit
        )
        
        return {
            "success": True,
            "mistakes": mistakes,
            "total": len(mistakes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错题失败: {str(e)}")


@app.get("/api/v2/mistakes/stats")
async def get_mistake_stats(user: dict = Depends(get_current_user)):
    """获取错题统计"""
    user_id = user["user_id"]
    
    try:
        stats = MistakeManager.get_mistake_stats(user_id)
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@app.post("/api/v2/mistakes/{subject_id}/review")
async def mark_mistake_reviewed(
    subject_id: str,
    user: dict = Depends(get_current_user)
):
    """标记错题为已复习"""
    try:
        success = MistakeManager.update_review_status(subject_id)
        return {
            "success": success,
            "message": "复习记录已更新"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


# ---------------------------
# 3. 试卷生成增强API
# ---------------------------

class PaperGenerateRequest(BaseModel):
    """生成试卷请求（增强版）"""
    subject: str  # 学科
    grade: str  # 年级
    paper_title: str
    question_types: List[str]  # 题型列表
    difficulty: str = "中等"
    total_score: float = 100.0
    duration_minutes: int = 90
    knowledge_points: Optional[List[str]] = None


@app.post("/api/v2/papers/generate")
async def generate_paper_with_subject_grade(
    request: PaperGenerateRequest,
    user: dict = Depends(get_current_user)
):
    """
    生成试卷（支持学科和年级选择）
    
    V25.2 新功能：
    - 自主选择学科
    - 自主选择年级
    - 基于知识点智能选题
    """
    user_id = user["user_id"]
    
    try:
        # 1. 创建试卷
        exam_id = ExamManager.create_exam(
            exam_title=request.paper_title,
            exam_content=f"{request.subject} - {request.grade}"
        )
        
        # 2. 构建AI提示词生成题目
        prompt = f"""请为{request.grade}学生生成一份{request.subject}试卷。

【试卷信息】
- 标题：{request.paper_title}
- 学科：{request.subject}
- 年级：{request.grade}
- 难度：{request.difficulty}
- 总分：{request.total_score}分
- 时长：{request.duration_minutes}分钟
- 题型：{', '.join(request.question_types)}

【知识点要求】
{', '.join(request.knowledge_points) if request.knowledge_points else '综合知识'}

【输出要求】
请生成5-10道题目，每道题包含：
1. 题目内容（可使用LaTeX公式）
2. 分值
3. 答案
4. 解析

格式：
---题目1---
题目内容：[题目内容]
分值：[分数]
答案：[答案]
解析：[解析]
知识点：[知识点]

---题目2---
...
"""
        
        # 3. 调用AI生成题目
        response = dashscope.MultiModalConversation.call(
            model='qwen-vl-max',
            messages=[{'role': 'user', 'content': prompt}]
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="AI生成题目失败")
        
        ai_response = response.output.choices[0].message.content[0]['text']
        
        # 打印AI响应以便调试
        print(f"\n{'='*70}")
        print("[AI响应内容预览]")
        print(ai_response[:500])
        print(f"{'='*70}\n")
        
        # 4. 解析题目并保存到数据库
        question_ids = []
        
        # 解析AI生成的题目（按"---题目X---"或"题目X："分割）
        import re
        
        # 尝试多种分割模式
        questions_text = []
        
        # 模式1：---题目X---
        if '---题目' in ai_response:
            questions_text = re.split(r'---题目\d+---', ai_response)
            print(f"[题目生成] 使用模式1分割（---题目X---）")
        # 模式2：题目X：
        elif re.search(r'题目\d+[：:]', ai_response):
            questions_text = re.split(r'题目\d+[：:]', ai_response)
            print(f"[题目生成] 使用模式2分割（题目X：）")
        # 模式3：【题目X】
        elif re.search(r'【题目\d+】', ai_response):
            questions_text = re.split(r'【题目\d+】', ai_response)
            print(f"[题目生成] 使用模式3分割（【题目X】）")
        else:
            # 如果没有找到分隔符，直接使用完整响应
            questions_text = [ai_response]
            print(f"[题目生成] 未找到分隔符，使用完整响应")
        
        questions_text = [q.strip() for q in questions_text if q.strip()]
        
        print(f"[题目生成] 解析到 {len(questions_text)} 道题目")
        
        # 为每道题目创建单独的记录
        for idx, question_text in enumerate(questions_text, 1):
            try:
                # 提取题目信息
                title = f"{request.paper_title}_第{idx}题"
                
                # 尝试提取知识点
                knowledge_points = []
                kp_match = re.search(r'知识点[：:](.*?)(?:\n|$)', question_text)
                if kp_match:
                    kp_text = kp_match.group(1).strip()
                    knowledge_points = [kp.strip() for kp in re.split(r'[,，、]', kp_text) if kp.strip()]
                
                # 提取答案
                answer = ""
                answer_match = re.search(r'答案[：:](.*?)(?=解析[：:]|知识点[：:]|$)', question_text, re.DOTALL)
                if answer_match:
                    answer = answer_match.group(1).strip()
                
                # 创建题目记录
                subject_id = SubjectManager.create_subject(
                    subject_title=title,
                    subject_desc=question_text[:500],  # 题目描述（截取前500字符）
                    solve=question_text,  # 完整题目内容
                    answer=answer,  # 答案
                    subject_type="generated",  # 标记为生成的题目
                    subject_name=request.subject,  # 学科
                    knowledge_points=json.dumps(knowledge_points, ensure_ascii=False) if knowledge_points else None
                )
                question_ids.append(subject_id)
                
                # 关联到试卷和用户
                ExamManager.link_user_exam_subject(user_id, exam_id, subject_id)
                
                print(f"[题目生成] ✓ 保存题目 {idx}: {title}")
            
            except Exception as e:
                print(f"[题目生成] ⚠️ 保存题目 {idx} 失败: {e}")
                continue
        
        # 如果没有成功解析任何题目，至少保存完整的AI响应
        if not question_ids:
            print("[题目生成] ⚠️ 未能解析出单独题目，保存完整响应")
            subject_id = SubjectManager.create_subject(
                subject_title=f"{request.paper_title}_完整试卷",
                subject_desc=ai_response[:1000],
                solve=ai_response,
                subject_type="generated",
                subject_name=request.subject
            )
            question_ids.append(subject_id)
            ExamManager.link_user_exam_subject(user_id, exam_id, subject_id)
        
        return {
            "success": True,
            "exam_id": exam_id,
            "subject": request.subject,
            "grade": request.grade,
            "question_ids": question_ids,
            "questions_count": len(question_ids),  # 实际生成的题目数量
            "questions_preview": ai_response,
            "message": f"试卷生成成功，共生成 {len(question_ids)} 道题目"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 试卷生成失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"试卷生成失败: {str(e)}")


# ==============================================================================
# 启动服务
# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

