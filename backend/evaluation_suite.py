"""
==============================================================================
沐梧AI解题系统 - 模型能力评估框架
==============================================================================
功能：
- 记录每次AI交互的评测数据
- 多维度评分系统
- 自动生成对比测试报告
==============================================================================
"""

import os
import csv
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, asdict, field
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ==============================================================================
# 配置
# ==============================================================================

# 评测数据存储目录
EVALUATION_DATA_DIR = Path("evaluation_data")
EVALUATION_DATA_DIR.mkdir(exist_ok=True)

# CSV文件路径
EVALUATION_CSV = EVALUATION_DATA_DIR / "evaluation_results.csv"

# 报告输出目录
REPORTS_DIR = Path("evaluation_reports")
REPORTS_DIR.mkdir(exist_ok=True)

# ==============================================================================
# 数据结构定义
# ==============================================================================

TaskType = Literal["solve", "review", "generate"]

@dataclass
class EvaluationRecord:
    """单次评测记录"""
    
    # 基本信息
    record_id: str
    model_name: str
    task_type: TaskType
    timestamp: str
    
    # 输入输出
    input_prompt: str
    input_image_path: Optional[str]
    raw_output: str
    
    # 通用评分 (1-5分)
    instruction_following_score: float = 0.0  # 指令遵循
    format_correction_score: float = 0.0      # 格式正确性
    hallucination_score: float = 0.0          # 幻觉检测（5分=无幻觉）
    
    # 解题任务评分
    ocr_accuracy_score: float = 0.0           # OCR准确率
    correctness_score: float = 0.0            # 答案正确性
    reasoning_quality_score: float = 0.0      # 逻辑推理质量
    
    # 批改任务评分
    error_detection_score: float = 0.0        # 错误检测能力
    explanation_clarity_score: float = 0.0    # 解析清晰度
    knowledge_point_accuracy_score: float = 0.0  # 知识点提取准确性
    
    # 生题任务评分
    relevance_score: float = 0.0              # 题目相关性
    creativity_difficulty_score: float = 0.0  # 创新与难度
    answer_integrity_score: float = 0.0       # 答案完整性
    
    # 定性记录
    notes: str = ""                           # 测试人员备注
    typical_failures: List[str] = field(default_factory=list)  # 典型失败案例
    
    # 元数据
    response_time_seconds: float = 0.0        # 响应时间
    token_count: int = 0                      # Token数量
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        # 将列表转换为JSON字符串以便存储
        data['typical_failures'] = json.dumps(data['typical_failures'], ensure_ascii=False)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EvaluationRecord':
        """从字典创建实例"""
        if isinstance(data['typical_failures'], str):
            data['typical_failures'] = json.loads(data['typical_failures'])
        return cls(**data)


# ==============================================================================
# 评分系统
# ==============================================================================

class EvaluationScorer:
    """评分系统（人工辅助）"""
    
    @staticmethod
    def score_task(
        model_output: str,
        task_type: TaskType,
        ground_truth: Optional[Dict] = None,
        manual_scores: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        对任务进行评分
        
        Args:
            model_output: 模型输出
            task_type: 任务类型
            ground_truth: 真值数据（如果有）
            manual_scores: 人工评分（如果已评）
        
        Returns:
            Dict[str, float]: 各维度评分
        """
        scores = {}
        
        # 如果提供了人工评分，直接使用
        if manual_scores:
            return manual_scores
        
        # 否则进行自动评分（基于规则，后续可人工调整）
        
        # 通用维度自动评分
        scores['instruction_following_score'] = EvaluationScorer._auto_score_instruction_following(
            model_output, task_type
        )
        scores['format_correction_score'] = EvaluationScorer._auto_score_format(model_output)
        scores['hallucination_score'] = EvaluationScorer._auto_score_hallucination(model_output)
        
        # 根据任务类型评分
        if task_type == "solve":
            scores['ocr_accuracy_score'] = 0.0  # 需要人工评分
            scores['correctness_score'] = 0.0   # 需要人工评分
            scores['reasoning_quality_score'] = EvaluationScorer._auto_score_reasoning(model_output)
        
        elif task_type == "review":
            scores['error_detection_score'] = 0.0  # 需要人工评分
            scores['explanation_clarity_score'] = EvaluationScorer._auto_score_clarity(model_output)
            scores['knowledge_point_accuracy_score'] = 0.0  # 需要人工评分
        
        elif task_type == "generate":
            scores['relevance_score'] = 0.0  # 需要人工评分
            scores['creativity_difficulty_score'] = 0.0  # 需要人工评分
            scores['answer_integrity_score'] = EvaluationScorer._auto_score_answer_integrity(model_output)
        
        return scores
    
    @staticmethod
    def _auto_score_instruction_following(output: str, task_type: TaskType) -> float:
        """自动评分：指令遵循"""
        score = 5.0
        
        # 检查是否包含明显违反指令的情况
        if "抱歉" in output and "无法" in output:
            score -= 1.0
        
        # 检查是否按照任务类型正确输出
        if task_type == "solve" and "解答" not in output and "解析" not in output:
            score -= 0.5
        
        return max(1.0, score)
    
    @staticmethod
    def _auto_score_format(output: str) -> float:
        """自动评分：格式正确性"""
        score = 5.0
        
        # 检查LaTeX公式格式
        if "$" in output or "\\(" in output:
            # 检查配对
            dollar_count = output.count("$")
            if dollar_count % 2 != 0:
                score -= 1.0  # LaTeX未配对
        
        # 检查Markdown格式
        if "##" in output or "**" in output:
            score += 0.5  # 使用了Markdown格式
        
        return min(5.0, max(1.0, score))
    
    @staticmethod
    def _auto_score_hallucination(output: str) -> float:
        """自动评分：幻觉检测（5分=无幻觉）"""
        score = 5.0
        
        # 检查常见的幻觉特征
        hallucination_keywords = [
            "根据我看到的图片", "图片中显示", "从图片可以看出"
        ]
        
        # 如果输出过短，可能是有问题的
        if len(output) < 50:
            score -= 1.0
        
        return max(1.0, score)
    
    @staticmethod
    def _auto_score_reasoning(output: str) -> float:
        """自动评分：逻辑推理质量"""
        score = 3.0  # 基础分
        
        # 检查是否有步骤标记
        step_markers = ["步骤", "第一", "第二", "首先", "然后", "最后", "因此"]
        step_count = sum(1 for marker in step_markers if marker in output)
        score += min(step_count * 0.3, 2.0)
        
        # 检查长度（更详细通常更好）
        if len(output) > 500:
            score += 0.5
        
        return min(5.0, max(1.0, score))
    
    @staticmethod
    def _auto_score_clarity(output: str) -> float:
        """自动评分：清晰度"""
        score = 3.0
        
        # 检查是否有结构化输出
        if "**" in output or "##" in output:
            score += 1.0
        
        # 检查是否有逻辑连接词
        connectors = ["因为", "所以", "但是", "然而", "因此", "由于"]
        if any(conn in output for conn in connectors):
            score += 0.5
        
        return min(5.0, max(1.0, score))
    
    @staticmethod
    def _auto_score_answer_integrity(output: str) -> float:
        """自动评分：答案完整性"""
        score = 3.0
        
        # 检查是否包含答案标记
        if "答案" in output or "解析" in output:
            score += 1.0
        
        # 检查是否有详细解释
        if len(output) > 300:
            score += 1.0
        
        return min(5.0, max(1.0, score))


# ==============================================================================
# 数据记录
# ==============================================================================

class EvaluationLogger:
    """评测数据记录器"""
    
    def __init__(self, csv_path: Path = EVALUATION_CSV):
        self.csv_path = csv_path
        self._init_csv()
    
    def _init_csv(self):
        """初始化CSV文件"""
        if not self.csv_path.exists():
            # 创建CSV文件并写入表头
            record = EvaluationRecord(
                record_id="",
                model_name="",
                task_type="solve",
                timestamp="",
                input_prompt="",
                input_image_path=None,
                raw_output=""
            )
            
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=record.to_dict().keys())
                writer.writeheader()
            
            print(f"✅ 初始化评测CSV文件: {self.csv_path}")
    
    def log_evaluation(self, record: EvaluationRecord) -> None:
        """
        记录一次评测
        
        Args:
            record: 评测记录
        """
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=record.to_dict().keys())
            writer.writerow(record.to_dict())
        
        print(f"✅ [评测记录] {record.model_name} - {record.task_type} - {record.record_id}")
    
    def load_all_records(self) -> List[EvaluationRecord]:
        """加载所有评测记录"""
        records = []
        
        if not self.csv_path.exists():
            return records
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 转换数值字段
                for key in row:
                    if 'score' in key or key == 'response_time_seconds':
                        row[key] = float(row[key]) if row[key] else 0.0
                    elif key == 'token_count':
                        row[key] = int(row[key]) if row[key] else 0
                
                records.append(EvaluationRecord.from_dict(row))
        
        return records
    
    def get_records_by_model(self, model_name: str) -> List[EvaluationRecord]:
        """获取特定模型的记录"""
        all_records = self.load_all_records()
        return [r for r in all_records if r.model_name == model_name]
    
    def get_records_by_task(self, task_type: TaskType) -> List[EvaluationRecord]:
        """获取特定任务类型的记录"""
        all_records = self.load_all_records()
        return [r for r in all_records if r.task_type == task_type]


# ==============================================================================
# 报告生成
# ==============================================================================

class ReportGenerator:
    """评测报告生成器"""
    
    def __init__(self, logger: EvaluationLogger):
        self.logger = logger
    
    def generate_report(self, output_path: Optional[Path] = None) -> str:
        """
        生成完整的对比测试报告
        
        Args:
            output_path: 报告输出路径，默认为 evaluation_reports/report_{timestamp}.md
        
        Returns:
            str: 报告内容
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = REPORTS_DIR / f"evaluation_report_{timestamp}.md"
        
        records = self.logger.load_all_records()
        
        if not records:
            return "❌ 没有可用的评测数据"
        
        # 使用pandas进行数据分析
        df = pd.DataFrame([r.to_dict() for r in records])
        
        # 开始构建报告
        report = []
        report.append("# 沐梧AI解题系统 - 大模型对比评测报告\n")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**评测样本数**: {len(records)}\n")
        report.append(f"**涉及模型数**: {df['model_name'].nunique()}\n")
        report.append("\n---\n")
        
        # 1. 总体表现概览
        report.append(self._generate_executive_summary(df))
        
        # 2. 综合评分对比表
        report.append(self._generate_comparison_table(df))
        
        # 3. 分任务详细分析
        report.append(self._generate_task_analysis(df))
        
        # 4. 模型问题记录
        report.append(self._generate_issues_log(records))
        
        # 5. 最终推荐
        report.append(self._generate_recommendation(df))
        
        # 6. 附录：原始数据统计
        report.append(self._generate_statistics_appendix(df))
        
        # 保存报告
        report_content = "\n".join(report)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ 评测报告已生成: {output_path}")
        return report_content
    
    def _generate_executive_summary(self, df: pd.DataFrame) -> str:
        """生成总体表现概览"""
        section = []
        section.append("## 📊 总体表现概览 (Executive Summary)\n")
        
        # 计算每个模型的综合得分
        score_columns = [col for col in df.columns if 'score' in col]
        
        model_scores = {}
        for model in df['model_name'].unique():
            model_df = df[df['model_name'] == model]
            avg_score = model_df[score_columns].mean().mean()
            model_scores[model] = avg_score
        
        # 排序
        sorted_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
        
        section.append(f"### 🏆 综合排名\n")
        for rank, (model, score) in enumerate(sorted_models, 1):
            section.append(f"{rank}. **{model}** - 综合得分: {score:.2f}/5.0\n")
        
        section.append("\n### 💡 关键发现\n")
        
        best_model = sorted_models[0][0]
        section.append(f"- **最佳综合表现**: {best_model}\n")
        
        # 成本分析（基于模型名称判断）
        if "32b" in best_model.lower():
            section.append(f"- **性价比优选**: {best_model}（32B模型，成本低）\n")
        elif "235b" in best_model.lower():
            section.append(f"- **高性能选择**: {best_model}（235B模型，推理能力强）\n")
        
        section.append("\n---\n")
        return "\n".join(section)
    
    def _generate_comparison_table(self, df: pd.DataFrame) -> str:
        """生成综合评分对比表"""
        section = []
        section.append("## 📈 综合评分对比表\n")
        
        # 定义评分维度
        dimensions = {
            "通用能力": [
                'instruction_following_score',
                'format_correction_score',
                'hallucination_score'
            ],
            "解题能力": [
                'ocr_accuracy_score',
                'correctness_score',
                'reasoning_quality_score'
            ],
            "批改能力": [
                'error_detection_score',
                'explanation_clarity_score',
                'knowledge_point_accuracy_score'
            ],
            "生题能力": [
                'relevance_score',
                'creativity_difficulty_score',
                'answer_integrity_score'
            ]
        }
        
        # 按任务类型生成对比表
        for task_type in ['solve', 'review', 'generate']:
            task_df = df[df['task_type'] == task_type]
            
            if len(task_df) == 0:
                continue
            
            task_name_map = {
                'solve': '🔍 解题任务',
                'review': '✏️ 批改任务',
                'generate': '📝 生题任务'
            }
            
            section.append(f"### {task_name_map[task_type]}\n")
            
            # 构建表格
            table_header = "| 模型 | 平均分 |"
            table_sep = "|------|--------|"
            
            # 添加相关维度列
            relevant_scores = []
            if task_type == 'solve':
                relevant_scores = dimensions["通用能力"] + dimensions["解题能力"]
            elif task_type == 'review':
                relevant_scores = dimensions["通用能力"] + dimensions["批改能力"]
            elif task_type == 'generate':
                relevant_scores = dimensions["通用能力"] + dimensions["生题能力"]
            
            # 简化表头
            score_names = {
                'instruction_following_score': '指令遵循',
                'format_correction_score': '格式正确',
                'hallucination_score': '无幻觉',
                'ocr_accuracy_score': 'OCR准确',
                'correctness_score': '答案正确',
                'reasoning_quality_score': '推理质量',
                'error_detection_score': '错误检测',
                'explanation_clarity_score': '解析清晰',
                'knowledge_point_accuracy_score': '知识点准确',
                'relevance_score': '题目相关',
                'creativity_difficulty_score': '创新难度',
                'answer_integrity_score': '答案完整'
            }
            
            for score in relevant_scores:
                if score in score_names:
                    table_header += f" {score_names[score]} |"
                    table_sep += "--------|"
            
            section.append(table_header)
            section.append(table_sep)
            
            # 填充数据
            for model in task_df['model_name'].unique():
                model_df = task_df[task_df['model_name'] == model]
                row = f"| {model} |"
                
                # 计算平均分
                avg_score = model_df[relevant_scores].mean().mean()
                row += f" **{avg_score:.2f}** |"
                
                # 各维度得分
                for score in relevant_scores:
                    score_val = model_df[score].mean()
                    row += f" {score_val:.2f} |"
                
                section.append(row)
            
            section.append("\n")
        
        section.append("---\n")
        return "\n".join(section)
    
    def _generate_task_analysis(self, df: pd.DataFrame) -> str:
        """生成分任务详细分析"""
        section = []
        section.append("## 🔬 分任务详细分析\n")
        
        task_names = {
            'solve': '解题任务',
            'review': '批改任务',
            'generate': '生题任务'
        }
        
        for task_type in ['solve', 'review', 'generate']:
            task_df = df[df['task_type'] == task_type]
            
            if len(task_df) == 0:
                continue
            
            section.append(f"### {task_names[task_type]}\n")
            section.append(f"**样本数**: {len(task_df)}\n\n")
            
            # 各模型表现
            for model in task_df['model_name'].unique():
                model_df = task_df[task_df['model_name'] == model]
                section.append(f"#### {model}\n")
                section.append(f"- 样本数: {len(model_df)}\n")
                section.append(f"- 平均响应时间: {model_df['response_time_seconds'].mean():.2f}秒\n")
                section.append(f"- 平均Token数: {model_df['token_count'].mean():.0f}\n")
                section.append("\n")
            
            section.append("\n")
        
        section.append("---\n")
        return "\n".join(section)
    
    def _generate_issues_log(self, records: List[EvaluationRecord]) -> str:
        """生成模型问题记录"""
        section = []
        section.append("## ⚠️ 模型问题记录 (Qualitative Issues Log)\n")
        section.append("*此部分记录了测试中发现的典型问题，可作为Prompt优化或微调的依据*\n\n")
        
        # 按模型分组
        model_issues = {}
        for record in records:
            if record.notes or record.typical_failures:
                if record.model_name not in model_issues:
                    model_issues[record.model_name] = []
                
                issue_entry = {
                    'task_type': record.task_type,
                    'notes': record.notes,
                    'failures': record.typical_failures
                }
                model_issues[record.model_name].append(issue_entry)
        
        if not model_issues:
            section.append("*暂无记录的问题*\n")
        else:
            for model, issues in model_issues.items():
                section.append(f"### {model}\n")
                
                for idx, issue in enumerate(issues, 1):
                    section.append(f"**问题 #{idx}** ({issue['task_type']})\n")
                    if issue['notes']:
                        section.append(f"- 描述: {issue['notes']}\n")
                    if issue['failures']:
                        section.append(f"- 典型失败:\n")
                        for failure in issue['failures']:
                            section.append(f"  - {failure}\n")
                    section.append("\n")
        
        section.append("---\n")
        return "\n".join(section)
    
    def _generate_recommendation(self, df: pd.DataFrame) -> str:
        """生成最终推荐"""
        section = []
        section.append("## 🎯 最终推荐\n")
        
        # 计算综合得分
        score_columns = [col for col in df.columns if 'score' in col]
        model_scores = {}
        for model in df['model_name'].unique():
            model_df = df[df['model_name'] == model]
            avg_score = model_df[score_columns].mean().mean()
            model_scores[model] = avg_score
        
        best_model = max(model_scores, key=model_scores.get)
        
        section.append(f"### 推荐模型: **{best_model}**\n")
        section.append(f"**综合得分**: {model_scores[best_model]:.2f}/5.0\n\n")
        
        section.append("### 推荐理由\n")
        
        # 根据模型名称推断特点
        if "32b-instruct" in best_model.lower():
            section.append("- ✅ **指令遵循能力强** (SIFO评分高)\n")
            section.append("- ✅ **性价比优秀** (32B参数量，推理成本低)\n")
            section.append("- ✅ **适合生产部署** (直接指令执行，响应快)\n")
        elif "32b-thinking" in best_model.lower():
            section.append("- ✅ **思考链推理** (适合复杂问题)\n")
            section.append("- ✅ **性价比优秀** (32B参数量)\n")
            section.append("- ⚠️ **响应可能较慢** (需要思考时间)\n")
        elif "235b" in best_model.lower():
            section.append("- ✅ **高性能推理** (AIME25/LCB评分高)\n")
            section.append("- ✅ **OCR能力强** (文字识别准确)\n")
            section.append("- ⚠️ **资源要求高** (235B参数量，需要更多GPU)\n")
        
        section.append("\n### 部署建议\n")
        section.append("1. **开发/测试环境**: 使用32B模型（快速迭代，成本低）\n")
        section.append("2. **生产环境**: 根据业务需求选择\n")
        section.append("   - 高并发场景 → 32B-Instruct\n")
        section.append("   - 高准确率需求 → 235B系列\n")
        section.append("3. **微调方向**: 根据\"模型问题记录\"进行针对性优化\n")
        
        section.append("\n---\n")
        return "\n".join(section)
    
    def _generate_statistics_appendix(self, df: pd.DataFrame) -> str:
        """生成统计附录"""
        section = []
        section.append("## 📎 附录：原始数据统计\n")
        
        section.append("### 数据概览\n")
        section.append(f"- 总样本数: {len(df)}\n")
        section.append(f"- 模型数: {df['model_name'].nunique()}\n")
        section.append(f"- 任务类型分布:\n")
        for task_type in df['task_type'].unique():
            count = len(df[df['task_type'] == task_type])
            section.append(f"  - {task_type}: {count} ({count/len(df)*100:.1f}%)\n")
        
        section.append("\n### 性能统计\n")
        section.append(f"- 平均响应时间: {df['response_time_seconds'].mean():.2f}秒\n")
        section.append(f"- 平均Token数: {df['token_count'].mean():.0f}\n")
        
        section.append("\n---\n")
        section.append("*报告生成完毕*\n")
        
        return "\n".join(section)


# ==============================================================================
# 便捷函数
# ==============================================================================

def create_evaluation_record(
    model_name: str,
    task_type: TaskType,
    input_prompt: str,
    raw_output: str,
    input_image_path: Optional[str] = None,
    response_time: float = 0.0,
    token_count: int = 0,
    manual_scores: Optional[Dict[str, float]] = None,
    notes: str = "",
    typical_failures: Optional[List[str]] = None
) -> EvaluationRecord:
    """
    创建评测记录（便捷函数）
    
    Args:
        model_name: 模型名称
        task_type: 任务类型
        input_prompt: 输入提示
        raw_output: 原始输出
        input_image_path: 输入图片路径
        response_time: 响应时间
        token_count: Token数量
        manual_scores: 人工评分
        notes: 备注
        typical_failures: 典型失败
    
    Returns:
        EvaluationRecord: 评测记录
    """
    # 生成记录ID
    record_id = f"{model_name}_{task_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 自动评分
    scorer = EvaluationScorer()
    scores = scorer.score_task(raw_output, task_type, manual_scores=manual_scores)
    
    # 创建记录
    record = EvaluationRecord(
        record_id=record_id,
        model_name=model_name,
        task_type=task_type,
        timestamp=datetime.now().isoformat(),
        input_prompt=input_prompt,
        input_image_path=input_image_path,
        raw_output=raw_output,
        response_time_seconds=response_time,
        token_count=token_count,
        notes=notes,
        typical_failures=typical_failures or [],
        **scores
    )
    
    return record


def quick_evaluate_and_log(
    model_name: str,
    task_type: TaskType,
    input_prompt: str,
    raw_output: str,
    **kwargs
) -> None:
    """
    快速评估并记录（一步完成）
    
    Args:
        model_name: 模型名称
        task_type: 任务类型
        input_prompt: 输入提示
        raw_output: 模型输出
        **kwargs: 其他参数（传递给create_evaluation_record）
    """
    logger = EvaluationLogger()
    record = create_evaluation_record(
        model_name=model_name,
        task_type=task_type,
        input_prompt=input_prompt,
        raw_output=raw_output,
        **kwargs
    )
    logger.log_evaluation(record)


# ==============================================================================
# 测试代码
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("评测框架测试")
    print("=" * 70 + "\n")
    
    # 创建测试数据
    logger = EvaluationLogger()
    
    # 模拟几条评测记录
    test_models = ["qwen-vl-max", "qwen3-vl-32b-instruct", "qwen3-vl-235b-a22b-thinking"]
    
    for model in test_models:
        for task_type in ["solve", "review"]:
            quick_evaluate_and_log(
                model_name=model,
                task_type=task_type,
                input_prompt="测试提示",
                raw_output="测试输出内容",
                notes="这是一个测试记录",
                response_time=2.5,
                token_count=150
            )
    
    print(f"\n✅ 已生成 {len(test_models) * 2} 条测试记录\n")
    
    # 生成报告
    generator = ReportGenerator(logger)
    report = generator.generate_report()
    
    print("\n📄 报告预览（前500字符）:")
    print(report[:500])
    print("...\n")

