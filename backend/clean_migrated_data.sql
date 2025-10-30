-- ==============================================================================
-- 清空已迁移的测试数据（用于重新迁移）
-- ==============================================================================

USE edu;

-- 显示当前数据统计
SELECT '迁移前数据统计' as info;
SELECT 'subject表' as 表名, COUNT(*) as 记录数 FROM subject;
SELECT 'exam表' as 表名, COUNT(*) as 记录数 FROM exam;
SELECT 'user_exam表' as 表名, COUNT(*) as 记录数 FROM user_exam;
SELECT 'user表' as 表名, COUNT(*) as 记录数, GROUP_CONCAT(account) as 账号列表 FROM user;

-- 清空demo_user的相关数据
SET @demo_user_id = (SELECT user_id FROM user WHERE account = 'demo_user');

-- 删除用户的答题记录
DELETE FROM user_exam WHERE user_info = @demo_user_id;

-- 删除用户的题目（通过exam关联）
DELETE s FROM subject s
WHERE s.subject_id IN (
    SELECT DISTINCT ue.subject_id FROM user_exam ue WHERE ue.user_info = @demo_user_id
);

-- 删除用户的试卷
DELETE FROM exam WHERE exam_id IN (
    SELECT DISTINCT ue.exam_id FROM user_exam ue WHERE ue.user_info = @demo_user_id
);

-- 可选：删除demo_user用户（如果要重新创建）
-- DELETE FROM user WHERE account = 'demo_user';

-- 显示清理后数据统计
SELECT '清理后数据统计' as info;
SELECT 'subject表' as 表名, COUNT(*) as 记录数 FROM subject;
SELECT 'exam表' as 表名, COUNT(*) as 记录数 FROM exam;
SELECT 'user_exam表' as 表名, COUNT(*) as 记录数 FROM user_exam;
SELECT 'user表' as 表名, COUNT(*) as 记录数, GROUP_CONCAT(account) as 账号列表 FROM user;

