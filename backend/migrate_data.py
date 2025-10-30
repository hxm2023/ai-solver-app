"""
==============================================================================
沐梧AI解题系统 - 数据迁移工具 (V25.1)
==============================================================================
功能：
- 将JSON格式的错题数据迁移到MySQL数据库
- 将JSON格式的生成题目迁移到MySQL数据库
- 为默认用户创建试卷并关联题目
==============================================================================
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from database import (
    init_database_pool,
    UserManager,
    SubjectManager,
    ExamManager,
    get_db_connection
)

# ==============================================================================
# 配置
# ==============================================================================

DATA_DIR = Path("simple_data")
MISTAKES_FILE = DATA_DIR / "mistakes.json"
QUESTIONS_FILE = DATA_DIR / "generated_questions.json"

# 默认测试用户
DEFAULT_USER_ACCOUNT = "demo_user"
DEFAULT_USER_PASSWORD = "demo123456"

# ==============================================================================
# 数据加载
# ==============================================================================

def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """加载JSON文件"""
    if not file_path.exists():
        print(f"⚠️  文件不存在: {file_path}")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ 加载文件成功: {file_path.name} ({len(data)} 条记录)")
            return data
    except Exception as e:
        print(f"❌ 加载文件失败: {file_path.name} - {e}")
        return []


# ==============================================================================
# 数据迁移函数
# ==============================================================================

def migrate_mistakes_to_subjects(user_id: str, exam_id: str) -> int:
    """
    迁移错题数据到subject表
    
    Args:
        user_id: 用户ID
        exam_id: 错题本试卷ID
    
    Returns:
        成功迁移的数量
    """
    print("\n" + "="*70)
    print("【迁移错题数据】")
    print("="*70)
    
    mistakes = load_json_file(MISTAKES_FILE)
    if not mistakes:
        print("⚠️  没有错题数据需要迁移")
        return 0
    
    success_count = 0
    
    for i, mistake in enumerate(mistakes, 1):
        try:
            # 提取错题信息
            question_text = mistake.get('question_text', '(无文字识别)')
            ai_analysis = mistake.get('ai_analysis', '')
            subject_name = mistake.get('subject', '未分类')
            grade = mistake.get('grade', '未分类')
            knowledge_points = mistake.get('knowledge_points', [])
            
            # 构建题目内容（包含错误答案和分析）
            subject_title = f"{question_text}\n\n【我的错误答案】\n{mistake.get('wrong_answer', '(未记录)')}"
            subject_desc = f"这是一道错题，需要重点复习"
            
            # 如果有图片，保存图片URL（这里简化处理，实际应该上传到云存储）
            image_base64 = mistake.get('image_base64', '')
            image_url = f"data:image/png;base64,{image_base64[:50]}..." if image_base64 else None
            
            # 创建题目记录
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 生成subject_id
                from uuid import uuid4
                subject_id = str(uuid4())
                
                # 插入subject表
                cursor.execute(
                    """INSERT INTO subject (
                        subject_id, subject_title, subject_desc, image_url, solve,
                        subject_type, difficulty, knowledge_points, subject_name, grade,
                        answer, explanation
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        subject_id,
                        subject_title,
                        subject_desc,
                        image_url,
                        ai_analysis,  # solve字段存储AI分析
                        'mistake',  # 题目类型：错题
                        '中等',  # 默认难度
                        json.dumps(knowledge_points, ensure_ascii=False),  # JSON格式
                        subject_name,
                        grade,
                        mistake.get('wrong_answer', ''),  # 用户的错误答案
                        ai_analysis  # 解析
                    )
                )
                
                # 关联用户-试卷-题目
                record_id = str(uuid4())
                cursor.execute(
                    """INSERT INTO user_exam (id, user_info, subject_id, exam_id, status)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (record_id, user_id, subject_id, exam_id, 'incorrect')
                )
                
                success_count += 1
                
                if i % 10 == 0 or i == len(mistakes):
                    print(f"  进度: {i}/{len(mistakes)} - 已迁移 {success_count} 条")
        
        except Exception as e:
            print(f"  ⚠️  迁移错题失败 (#{i}): {e}")
            continue
    
    print(f"\n✅ 错题迁移完成: {success_count}/{len(mistakes)} 条成功")
    return success_count


def migrate_questions_to_subjects(user_id: str, exam_id: str) -> int:
    """
    迁移生成题目到subject表
    
    Args:
        user_id: 用户ID
        exam_id: 练习题集试卷ID
    
    Returns:
        成功迁移的数量
    """
    print("\n" + "="*70)
    print("【迁移生成题目】")
    print("="*70)
    
    questions = load_json_file(QUESTIONS_FILE)
    if not questions:
        print("⚠️  没有生成题目需要迁移")
        return 0
    
    success_count = 0
    
    for i, question in enumerate(questions, 1):
        try:
            # 提取题目信息
            content = question.get('content', '')
            answer = question.get('answer', '')
            explanation = question.get('explanation', '')
            knowledge_points = question.get('knowledge_points', [])
            difficulty = question.get('difficulty', '中等')
            subject_name = question.get('subject', '数学')  # 默认数学
            
            # 创建题目记录
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 生成subject_id
                from uuid import uuid4
                subject_id = str(uuid4())
                
                # 插入subject表
                cursor.execute(
                    """INSERT INTO subject (
                        subject_id, subject_title, subject_desc, solve,
                        subject_type, difficulty, knowledge_points, subject_name,
                        answer, explanation
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        subject_id,
                        content,  # 题目内容
                        'AI生成的练习题',
                        answer,  # solve字段存储答案
                        'generated',  # 题目类型：生成题
                        difficulty,
                        json.dumps(knowledge_points, ensure_ascii=False),
                        subject_name,
                        answer,
                        explanation
                    )
                )
                
                # 关联用户-试卷-题目
                record_id = str(uuid4())
                cursor.execute(
                    """INSERT INTO user_exam (id, user_info, subject_id, exam_id, status)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (record_id, user_id, subject_id, exam_id, 'unanswered')
                )
                
                success_count += 1
                
                if i % 10 == 0 or i == len(questions):
                    print(f"  进度: {i}/{len(questions)} - 已迁移 {success_count} 条")
        
        except Exception as e:
            print(f"  ⚠️  迁移题目失败 (#{i}): {e}")
            continue
    
    print(f"\n✅ 题目迁移完成: {success_count}/{len(questions)} 条成功")
    return success_count


# ==============================================================================
# 主迁移流程
# ==============================================================================

def main():
    """主迁移流程"""
    print("\n" + "="*70)
    print("沐梧AI解题系统 - 数据迁移工具 V25.1")
    print("="*70)
    
    # 初始化数据库连接池
    print("\n[1/5] 初始化数据库连接...")
    init_database_pool()
    
    # 创建或获取默认用户
    print("\n[2/5] 创建默认测试用户...")
    user_result = UserManager.register(DEFAULT_USER_ACCOUNT, DEFAULT_USER_PASSWORD)
    
    if user_result["success"]:
        user_id = user_result["user_id"]
        print(f"✅ 用户创建成功: {DEFAULT_USER_ACCOUNT} (ID: {user_id})")
    else:
        # 用户已存在，尝试登录获取ID
        login_result = UserManager.login(DEFAULT_USER_ACCOUNT, DEFAULT_USER_PASSWORD)
        if login_result["success"]:
            user_id = login_result["user_id"]
            print(f"✅ 用户已存在，使用现有账号: {DEFAULT_USER_ACCOUNT} (ID: {user_id})")
        else:
            print(f"❌ 无法获取用户信息: {login_result['message']}")
            return
    
    # 创建错题本试卷
    print("\n[3/5] 创建错题本试卷...")
    mistake_exam_id = ExamManager.create_exam(
        exam_title=f"{DEFAULT_USER_ACCOUNT}的错题本",
        exam_content="记录所有错题，重点复习"
    )
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE exam SET exam_type = %s WHERE exam_id = %s",
            ('mistake_book', mistake_exam_id)
        )
    
    print(f"✅ 错题本创建成功 (ID: {mistake_exam_id})")
    
    # 创建练习题集试卷
    print("\n[4/5] 创建练习题集试卷...")
    practice_exam_id = ExamManager.create_exam(
        exam_title=f"{DEFAULT_USER_ACCOUNT}的练习题集",
        exam_content="AI生成的练习题目"
    )
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE exam SET exam_type = %s WHERE exam_id = %s",
            ('practice_set', practice_exam_id)
        )
    
    print(f"✅ 练习题集创建成功 (ID: {practice_exam_id})")
    
    # 迁移数据
    print("\n[5/5] 开始迁移数据...")
    
    # 迁移错题
    mistake_count = migrate_mistakes_to_subjects(user_id, mistake_exam_id)
    
    # 迁移生成题目
    question_count = migrate_questions_to_subjects(user_id, practice_exam_id)
    
    # 完成
    print("\n" + "="*70)
    print("🎉 数据迁移完成！")
    print("="*70)
    print(f"""
迁移统计：
- 用户账号: {DEFAULT_USER_ACCOUNT}
- 用户ID: {user_id}
- 错题本ID: {mistake_exam_id}
- 练习题集ID: {practice_exam_id}
- 迁移错题: {mistake_count} 条
- 迁移题目: {question_count} 条
- 总计: {mistake_count + question_count} 条

登录信息：
- 账号: {DEFAULT_USER_ACCOUNT}
- 密码: {DEFAULT_USER_PASSWORD}
""")
    
    print("✅ 您现在可以使用以上账号登录系统查看迁移的数据！")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  迁移被用户中断")
    except Exception as e:
        print(f"\n\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()

