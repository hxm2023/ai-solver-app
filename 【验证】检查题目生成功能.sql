-- ============================================================================
-- 题目生成功能验证SQL脚本
-- ============================================================================
-- 使用说明：在MySQL客户端或Navicat中执行此脚本，检查生成的题目
-- ============================================================================

USE ai_solver;

-- 1. 查看最近生成的题目（按创建时间倒序）
SELECT 
    subject_id AS '题目ID',
    subject_title AS '题目标题',
    subject_type AS '题目类型',
    subject_name AS '学科',
    grade AS '年级',
    difficulty AS '难度',
    SUBSTRING(subject_desc, 1, 50) AS '题目描述（前50字符）',
    created_at AS '创建时间'
FROM subject
WHERE subject_type = 'generated'
ORDER BY created_at DESC
LIMIT 20;

-- 2. 统计各学科生成的题目数量
SELECT 
    subject_name AS '学科',
    COUNT(*) AS '题目数量'
FROM subject
WHERE subject_type = 'generated'
GROUP BY subject_name
ORDER BY COUNT(*) DESC;

-- 3. 查看最近一次生成的试卷及其题目
SELECT 
    e.exam_id AS '试卷ID',
    e.exam_title AS '试卷名称',
    COUNT(DISTINCT s.subject_id) AS '题目数量',
    e.created_at AS '创建时间'
FROM exam e
LEFT JOIN user_exam ue ON e.exam_id = ue.exam_id
LEFT JOIN subject s ON ue.subject_id = s.subject_id
GROUP BY e.exam_id, e.exam_title, e.created_at
ORDER BY e.created_at DESC
LIMIT 10;

-- 4. 查看特定试卷的所有题目详情
-- （请将 'YOUR_EXAM_ID' 替换为实际的试卷ID）
-- SELECT 
--     s.subject_id AS '题目ID',
--     s.subject_title AS '题目标题',
--     s.subject_desc AS '题目描述',
--     s.answer AS '答案',
--     s.knowledge_points AS '知识点'
-- FROM subject s
-- JOIN user_exam ue ON s.subject_id = ue.subject_id
-- WHERE ue.exam_id = 'YOUR_EXAM_ID'
-- ORDER BY s.created_at;

-- 5. 检查是否有题目未关联到用户
SELECT 
    s.subject_id AS '题目ID',
    s.subject_title AS '题目标题',
    s.created_at AS '创建时间'
FROM subject s
LEFT JOIN user_exam ue ON s.subject_id = ue.subject_id
WHERE s.subject_type = 'generated' AND ue.user_info IS NULL
ORDER BY s.created_at DESC;

-- 6. 查看当前用户的所有生成题目
-- （请将 'YOUR_USER_ID' 替换为实际的用户ID）
-- SELECT 
--     s.subject_id AS '题目ID',
--     s.subject_title AS '题目标题',
--     s.subject_type AS '题目类型',
--     s.created_at AS '创建时间'
-- FROM subject s
-- JOIN user_exam ue ON s.subject_id = ue.subject_id
-- WHERE ue.user_info = 'YOUR_USER_ID' AND s.subject_type = 'generated'
-- ORDER BY s.created_at DESC;

-- ============================================================================
-- 预期结果说明
-- ============================================================================
-- 
-- 修复前：
--   查询1可能只返回1条记录，即使生成了多道题目
-- 
-- 修复后：
--   查询1应该返回与生成数量一致的记录（如生成5道题，返回5条记录）
--   每道题都有单独的subject_id、subject_title
--   subject_type都是'generated'
-- 
-- ============================================================================

