-- ==============================================================================
-- 修复 subject_title 字段长度限制
-- ==============================================================================

USE edu;

-- 修改 subject_title 为 LONGTEXT 类型（支持最大4GB）
ALTER TABLE subject MODIFY COLUMN subject_title LONGTEXT 
COMMENT '题目标题/题干（支持长文本）';

-- 同时修改其他可能过长的字段
ALTER TABLE subject MODIFY COLUMN subject_desc LONGTEXT 
COMMENT '题目描述';

ALTER TABLE subject MODIFY COLUMN solve LONGTEXT 
COMMENT '解答';

ALTER TABLE subject MODIFY COLUMN answer LONGTEXT 
COMMENT '标准答案';

ALTER TABLE subject MODIFY COLUMN explanation LONGTEXT 
COMMENT '题目解析';

-- 验证修改结果
SELECT 
    COLUMN_NAME, 
    COLUMN_TYPE, 
    CHARACTER_MAXIMUM_LENGTH 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'edu' 
  AND TABLE_NAME = 'subject' 
  AND COLUMN_NAME IN ('subject_title', 'subject_desc', 'solve', 'answer', 'explanation');

-- 预期结果：所有字段都应该是 longtext 类型

