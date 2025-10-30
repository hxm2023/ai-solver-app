-- ==============================================================================
-- 沐梧AI解题系统 - 数据库表结构升级脚本 (V25.2)
-- ==============================================================================
-- 新功能：
-- 1. 对话历史存储（连续对话功能）
-- 2. 错题本增强（自动保存错题、图片、解析、知识点）
-- 3. 试卷生成支持学科和年级选择
-- ==============================================================================

USE edu;

-- ==============================================================================
-- 1. 创建对话会话表 (chat_session)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS chat_session (
    session_id VARCHAR(64) PRIMARY KEY COMMENT '会话ID（UUID）',
    user_id VARCHAR(64) NOT NULL COMMENT '用户ID',
    title VARCHAR(200) DEFAULT '新对话' COMMENT '会话标题',
    mode VARCHAR(20) DEFAULT 'solve' COMMENT '对话模式：solve(解题), review(批改), ask(提问)',
    subject VARCHAR(50) DEFAULT '未分类' COMMENT '学科',
    grade VARCHAR(20) DEFAULT '未分类' COMMENT '年级',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted TINYINT(1) DEFAULT 0 COMMENT '是否删除（软删除）',
    
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_is_deleted (is_deleted),
    
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='AI对话会话表';

-- ==============================================================================
-- 2. 创建对话历史表 (chat_history)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS chat_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    role VARCHAR(20) NOT NULL COMMENT '角色：user(用户), assistant(AI)',
    content TEXT NOT NULL COMMENT '消息内容',
    image_url TEXT COMMENT '图片URL（如果有）',
    image_base64 MEDIUMTEXT COMMENT '图片Base64数据（可选存储）',
    message_type VARCHAR(20) DEFAULT 'text' COMMENT '消息类型：text(文本), image(图片), mixed(图文混合)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at),
    INDEX idx_role (role),
    
    FOREIGN KEY (session_id) REFERENCES chat_session(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='AI对话历史记录表';

-- ==============================================================================
-- 3. 扩展 subject 表（如果字段不存在则添加）
-- ==============================================================================

-- 添加题目图片URL字段（已有image_url，确保存在）
-- ALTER TABLE subject ADD COLUMN image_url TEXT COMMENT '题目原图URL';

-- 添加错题相关的额外信息字段
ALTER TABLE subject ADD COLUMN mistake_analysis TEXT COMMENT '错题分析（AI生成）';
ALTER TABLE subject ADD COLUMN user_mistake_text TEXT COMMENT '用户的错误答案';
ALTER TABLE subject ADD COLUMN correct_rate DECIMAL(5,2) DEFAULT 0.00 COMMENT '正确率（0-100）';
ALTER TABLE subject ADD COLUMN review_count INT DEFAULT 0 COMMENT '复习次数';
ALTER TABLE subject ADD COLUMN last_review_at DATETIME COMMENT '最后复习时间';

-- 确保知识点、答案、解析字段存在（V25.1可能已添加）
-- ALTER TABLE subject ADD COLUMN knowledge_points TEXT COMMENT '知识点列表（JSON数组格式）';
-- ALTER TABLE subject ADD COLUMN answer TEXT COMMENT '标准答案';
-- ALTER TABLE subject ADD COLUMN explanation TEXT COMMENT '题目解析';

-- ==============================================================================
-- 4. 创建知识点标签表（可选，用于统计和推荐）
-- ==============================================================================
CREATE TABLE IF NOT EXISTS knowledge_tag (
    tag_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '标签ID',
    tag_name VARCHAR(100) NOT NULL COMMENT '知识点名称',
    subject VARCHAR(50) NOT NULL COMMENT '所属学科',
    parent_tag_id INT DEFAULT NULL COMMENT '父标签ID（用于层级结构）',
    description TEXT COMMENT '标签描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    UNIQUE KEY uk_tag_subject (tag_name, subject),
    INDEX idx_subject (subject),
    INDEX idx_parent_tag (parent_tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='知识点标签表';

-- ==============================================================================
-- 5. 创建题目-知识点关联表
-- ==============================================================================
CREATE TABLE IF NOT EXISTS subject_knowledge_tag (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '关联ID',
    subject_id VARCHAR(64) NOT NULL COMMENT '题目ID',
    tag_id INT NOT NULL COMMENT '知识点标签ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    UNIQUE KEY uk_subject_tag (subject_id, tag_id),
    INDEX idx_subject_id (subject_id),
    INDEX idx_tag_id (tag_id),
    
    FOREIGN KEY (subject_id) REFERENCES subject(subject_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES knowledge_tag(tag_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='题目-知识点关联表';

-- ==============================================================================
-- 6. 创建试卷模板表（支持学科和年级）
-- ==============================================================================
CREATE TABLE IF NOT EXISTS exam_template (
    template_id VARCHAR(64) PRIMARY KEY COMMENT '模板ID',
    template_name VARCHAR(200) NOT NULL COMMENT '模板名称',
    subject VARCHAR(50) NOT NULL COMMENT '学科',
    grade VARCHAR(20) NOT NULL COMMENT '年级',
    description TEXT COMMENT '模板描述',
    total_score DECIMAL(6,2) DEFAULT 100.00 COMMENT '总分',
    duration_minutes INT DEFAULT 90 COMMENT '考试时长（分钟）',
    question_structure TEXT COMMENT '题型结构（JSON格式）',
    creator_id VARCHAR(64) COMMENT '创建者ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    is_public TINYINT(1) DEFAULT 0 COMMENT '是否公开',
    
    INDEX idx_subject_grade (subject, grade),
    INDEX idx_creator_id (creator_id),
    INDEX idx_is_public (is_public)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='试卷模板表';

-- ==============================================================================
-- 7. 扩展 exam 表（添加学科和年级字段）
-- ==============================================================================
ALTER TABLE exam ADD COLUMN subject VARCHAR(50) DEFAULT '未分类' COMMENT '学科';
ALTER TABLE exam ADD COLUMN grade VARCHAR(20) DEFAULT '未分类' COMMENT '年级';
ALTER TABLE exam ADD COLUMN total_score DECIMAL(6,2) DEFAULT 100.00 COMMENT '总分';
ALTER TABLE exam ADD COLUMN duration_minutes INT DEFAULT 90 COMMENT '考试时长（分钟）';
ALTER TABLE exam ADD COLUMN template_id VARCHAR(64) COMMENT '使用的模板ID';

-- ==============================================================================
-- 8. 创建学习统计表（可选，用于数据分析）
-- ==============================================================================
CREATE TABLE IF NOT EXISTS learning_stats (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '统计ID',
    user_id VARCHAR(64) NOT NULL COMMENT '用户ID',
    subject VARCHAR(50) NOT NULL COMMENT '学科',
    date DATE NOT NULL COMMENT '统计日期',
    total_questions INT DEFAULT 0 COMMENT '总题数',
    correct_questions INT DEFAULT 0 COMMENT '正确题数',
    mistake_questions INT DEFAULT 0 COMMENT '错题数',
    study_duration_minutes INT DEFAULT 0 COMMENT '学习时长（分钟）',
    ai_chat_count INT DEFAULT 0 COMMENT 'AI对话次数',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_user_subject_date (user_id, subject, date),
    INDEX idx_user_id (user_id),
    INDEX idx_date (date),
    INDEX idx_subject (subject),
    
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='学习统计表';

-- ==============================================================================
-- 9. 插入默认学科和年级数据
-- ==============================================================================

-- 插入常见学科
INSERT IGNORE INTO knowledge_tag (tag_name, subject, description) VALUES
('代数运算', '数学', '包括整式、分式、根式等运算'),
('函数', '数学', '一次函数、二次函数、指数函数等'),
('几何图形', '数学', '三角形、圆、立体几何等'),
('概率统计', '数学', '排列组合、概率、统计等'),
('力学', '物理', '牛顿定律、运动学、能量等'),
('电学', '物理', '电路、电磁感应等'),
('光学', '物理', '光的反射、折射等'),
('化学反应', '化学', '氧化还原、酸碱中和等'),
('元素周期表', '化学', '元素性质、周期律等'),
('有机化学', '化学', '烷烃、烯烃、醇等'),
('语法', '英语', '时态、语态、从句等'),
('阅读理解', '英语', '文章理解、推理判断等'),
('写作技巧', '语文', '记叙文、议论文、说明文等'),
('文言文', '语文', '古文阅读与翻译');

-- ==============================================================================
-- 10. 创建视图：用户错题统计
-- ==============================================================================
CREATE OR REPLACE VIEW v_user_mistake_stats AS
SELECT 
    ue.user_info AS user_id,
    s.subject_name AS subject,
    s.grade,
    COUNT(*) AS total_mistakes,
    COUNT(DISTINCT DATE(ue.answered_at)) AS mistake_days,
    AVG(s.difficulty) AS avg_difficulty,
    GROUP_CONCAT(DISTINCT s.knowledge_points) AS all_knowledge_points
FROM user_exam ue
JOIN subject s ON ue.subject_id = s.subject_id
WHERE s.subject_type = 'mistake'
GROUP BY ue.user_info, s.subject_name, s.grade;

-- ==============================================================================
-- 11. 创建触发器：自动更新会话更新时间
-- ==============================================================================
DELIMITER $$

CREATE TRIGGER IF NOT EXISTS trg_update_session_time
AFTER INSERT ON chat_history
FOR EACH ROW
BEGIN
    UPDATE chat_session 
    SET updated_at = CURRENT_TIMESTAMP
    WHERE session_id = NEW.session_id;
END$$

DELIMITER ;

-- ==============================================================================
-- 12. 验证表结构
-- ==============================================================================

-- 查看新创建的表
SHOW TABLES LIKE 'chat%';
SHOW TABLES LIKE 'knowledge%';
SHOW TABLES LIKE 'exam_template';

-- 查看表结构
DESC chat_session;
DESC chat_history;
DESC subject;
DESC exam;

-- 查看视图
SHOW CREATE VIEW v_user_mistake_stats;

-- ==============================================================================
-- 执行完成！
-- ==============================================================================
-- 【重要提示】
-- 
-- 1. 执行顺序：
--    - 先执行 database_schema_upgrade.sql（V25.1）
--    - 再执行本脚本 database_schema_v25.2.sql
-- 
-- 2. 错误处理：
--    - Error 1060: Duplicate column name（字段已存在）- 可忽略
--    - Error 1061: Duplicate key name（索引已存在）- 可忽略
--    - Error 1050: Table already exists（表已存在）- 可忽略
-- 
-- 3. 新增功能：
--    ✅ 对话历史存储（chat_session + chat_history）
--    ✅ 错题本增强（mistake_analysis、knowledge_points等）
--    ✅ 知识点标签系统（knowledge_tag）
--    ✅ 试卷模板支持学科和年级
--    ✅ 学习统计功能（可选）
-- 
-- 4. 验证成功标志：
--    - SHOW TABLES 能看到 chat_session、chat_history
--    - DESC subject 能看到 mistake_analysis 等新字段
--    - DESC exam 能看到 subject、grade 字段
-- 
-- ==============================================================================

