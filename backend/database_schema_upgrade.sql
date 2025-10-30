-- ==============================================================================
-- 沐梧AI解题系统 - 数据库表结构扩展脚本 (V25.1)
-- ==============================================================================
-- 用途：为现有数据库添加必要字段，以支持完整功能
-- 执行：在MySQL客户端或Navicat中连接到edu数据库后执行
-- ==============================================================================

USE edu;

-- ==============================================================================
-- 1. 扩展 subject 表（题目表）
-- ==============================================================================
-- 注意：如果列已存在，会报错1060(Duplicate column name)，这是正常的，可以忽略

-- 添加题目类型字段（区分错题、生成题、练习题）
ALTER TABLE subject ADD COLUMN subject_type VARCHAR(50) DEFAULT 'practice'
COMMENT '题目类型：mistake(错题), generated(生成题), practice(练习题)';

-- 添加难度字段
ALTER TABLE subject ADD COLUMN difficulty VARCHAR(20) DEFAULT '中等'
COMMENT '题目难度：简单、中等、困难';

-- 添加知识点字段（JSON格式存储）
ALTER TABLE subject ADD COLUMN knowledge_points TEXT
COMMENT '知识点列表（JSON数组格式）';

-- 添加学科字段
ALTER TABLE subject ADD COLUMN subject_name VARCHAR(50) DEFAULT '未分类'
COMMENT '学科名称：数学、物理、化学等';

-- 添加年级字段
ALTER TABLE subject ADD COLUMN grade VARCHAR(20) DEFAULT '未分类'
COMMENT '年级：高一、高二、高三等';

-- 添加创建时间字段
ALTER TABLE subject ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP
COMMENT '题目创建时间';

-- 添加更新时间字段
ALTER TABLE subject ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
COMMENT '题目更新时间';

-- 添加答案字段（独立存储答案）
ALTER TABLE subject ADD COLUMN answer TEXT
COMMENT '标准答案';

-- 添加解析字段（详细解题步骤）
ALTER TABLE subject ADD COLUMN explanation TEXT
COMMENT '题目解析';

-- ==============================================================================
-- 2. 扩展 exam 表（试卷表）
-- ==============================================================================

-- 添加创建时间字段
ALTER TABLE exam ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP
COMMENT '试卷创建时间';

-- 添加试卷类型字段
ALTER TABLE exam ADD COLUMN exam_type VARCHAR(50) DEFAULT 'custom'
COMMENT '试卷类型：mistake_book(错题本), practice_set(练习题集), test_paper(测试卷)';

-- ==============================================================================
-- 3. 扩展 user_exam 表（用户考试记录表）
-- ==============================================================================

-- 添加答题时间字段
ALTER TABLE user_exam ADD COLUMN answered_at DATETIME DEFAULT CURRENT_TIMESTAMP
COMMENT '答题时间';

-- 添加用户答案字段（用于记录学生的答案）
ALTER TABLE user_exam ADD COLUMN user_answer TEXT
COMMENT '用户提交的答案';

-- 添加答题状态字段（正确/错误/未答）
ALTER TABLE user_exam ADD COLUMN status VARCHAR(20) DEFAULT 'unanswered'
COMMENT '答题状态：correct(正确), incorrect(错误), unanswered(未答)';

-- ==============================================================================
-- 4. 创建索引（提升查询性能）
-- ==============================================================================
-- 注意：IF NOT EXISTS 在某些MySQL版本中可能不支持CREATE INDEX
-- 如果报错，可以忽略(1061 - Duplicate key name)或单独执行

-- subject表索引
CREATE INDEX idx_subject_type ON subject(subject_type);
CREATE INDEX idx_subject_name ON subject(subject_name);
CREATE INDEX idx_subject_grade ON subject(grade);
CREATE INDEX idx_subject_created ON subject(created_at);

-- user_exam表索引
CREATE INDEX idx_user_exam_user ON user_exam(user_info);
CREATE INDEX idx_user_exam_exam ON user_exam(exam_id);
CREATE INDEX idx_user_exam_subject ON user_exam(subject_id);

-- exam表索引
CREATE INDEX idx_exam_type ON exam(exam_type);
CREATE INDEX idx_exam_created ON exam(created_at);

-- ==============================================================================
-- 5. 验证表结构
-- ==============================================================================

-- 查看subject表结构
DESC subject;

-- 查看exam表结构
DESC exam;

-- 查看user_exam表结构
DESC user_exam;

-- ==============================================================================
-- 执行完成！
-- ==============================================================================
-- 【重要提示】
-- 
-- 1. 如果看到以下错误，这是正常的，可以忽略：
--    - Error 1060: Duplicate column name '字段名' (字段已存在)
--    - Error 1061: Duplicate key name '索引名' (索引已存在)
-- 
-- 2. 执行建议：
--    方式A：在Navicat中逐条执行（推荐）
--           - 选中一条语句，按F9执行
--           - 遇到1060/1061错误，继续执行下一条
--    
--    方式B：全部执行（快速）
--           - 选中全部，按F9执行
--           - 会看到多个错误提示，只要最后DESC表能看到新字段即可
-- 
-- 3. 验证成功：
--    执行 DESC subject; 应该看到新增字段：
--    - subject_type, difficulty, knowledge_points, subject_name, grade, etc.
-- 
-- ==============================================================================

