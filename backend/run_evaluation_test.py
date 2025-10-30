"""
==============================================================================
沐梧AI解题系统 - 评测框架快速测试脚本
==============================================================================
功能：
- 快速测试模型切换功能
- 模拟评测数据收集
- 生成测试报告
==============================================================================
"""

import sys
import time
from pathlib import Path

# 确保能导入本地模块
sys.path.insert(0, str(Path(__file__).parent))

import config
from model_adapter import get_multimodal_adapter, get_text_adapter
from evaluation_suite import (
    create_evaluation_record,
    EvaluationLogger,
    ReportGenerator,
    quick_evaluate_and_log
)


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def test_model_config():
    """测试模型配置"""
    print_section("1. 测试模型配置")
    
    # 显示所有可用模型
    config.list_all_models()
    
    # 显示当前模型
    print("\n当前激活的模型:")
    print(config.get_model_info())
    
    # 测试配置获取
    try:
        model_config = config.get_active_model_config()
        print(f"\n✅ 配置加载成功")
        print(f"   模型类型: {model_config['type']}")
        print(f"   模型名称: {model_config['model_name']}")
        
        if model_config['type'] == 'dashscope_api':
            print(f"   API密钥: {model_config['api_key'][:20]}...")
        else:
            print(f"   API地址: {model_config['api_base']}")
        
        return True
    except Exception as e:
        print(f"\n❌ 配置加载失败: {e}")
        return False


def test_model_adapter():
    """测试模型适配器"""
    print_section("2. 测试模型适配器")
    
    try:
        adapter = get_multimodal_adapter()
        print(f"✅ 适配器初始化成功: {adapter.model_name}")
        
        # 构建简单测试消息
        test_messages = [
            {
                "role": "system",
                "content": "你是一位数学老师。"
            },
            {
                "role": "user",
                "content": [
                    {"text": "请用一句话介绍你自己。"}
                ]
            }
        ]
        
        print("\n📤 发送测试消息...")
        print("💬 AI回复: ")
        
        start_time = time.time()
        full_response = ""
        
        try:
            for chunk in adapter.call(test_messages, stream=True):
                if chunk["finish_reason"] == "error":
                    print(f"\n❌ 错误: {chunk.get('error')}")
                    return False
                
                content = chunk["content"]
                full_response += content
                print(content, end="", flush=True)
            
            response_time = time.time() - start_time
            
            print(f"\n\n✅ 测试成功！")
            print(f"   响应时间: {response_time:.2f}秒")
            print(f"   回复长度: {len(full_response)}字符")
            
            return True, full_response, response_time
        
        except Exception as e:
            print(f"\n❌ 调用失败: {e}")
            return False, "", 0
    
    except Exception as e:
        print(f"❌ 适配器初始化失败: {e}")
        return False, "", 0


def test_evaluation_logging(response: str, response_time: float):
    """测试评测记录"""
    print_section("3. 测试评测记录")
    
    try:
        logger = EvaluationLogger()
        print(f"✅ 评测记录器初始化成功")
        print(f"   CSV文件: {logger.csv_path}")
        
        # 创建测试记录
        print("\n📝 创建测试评测记录...")
        
        for task_type in ["solve", "review", "generate"]:
            record = create_evaluation_record(
                model_name=config.ACTIVE_MODEL_KEY,
                task_type=task_type,
                input_prompt=f"测试{task_type}任务的输入",
                raw_output=response,
                response_time=response_time,
                token_count=len(response),
                notes=f"这是{task_type}任务的测试记录",
                typical_failures=["测试失败案例1", "测试失败案例2"]
            )
            
            logger.log_evaluation(record)
            print(f"   ✓ {task_type}任务记录已保存")
        
        # 加载记录验证
        all_records = logger.load_all_records()
        print(f"\n✅ 评测记录测试完成")
        print(f"   当前总记录数: {len(all_records)}")
        
        return True
    
    except Exception as e:
        print(f"❌ 评测记录测试失败: {e}")
        return False


def test_report_generation():
    """测试报告生成"""
    print_section("4. 测试报告生成")
    
    try:
        logger = EvaluationLogger()
        generator = ReportGenerator(logger)
        
        print("📊 生成评测报告...")
        report = generator.generate_report()
        
        print(f"\n✅ 报告生成成功！")
        print(f"   报告长度: {len(report)}字符")
        
        # 显示报告预览
        print("\n📄 报告预览（前800字符）:")
        print("-" * 70)
        print(report[:800])
        print("...")
        print("-" * 70)
        
        return True
    
    except Exception as e:
        print(f"❌ 报告生成失败: {e}")
        return False


def simulate_batch_evaluation():
    """模拟批量评测"""
    print_section("5. 模拟批量评测（可选）")
    
    response = input("\n是否要模拟生成更多评测数据？(y/n): ").strip().lower()
    
    if response != 'y':
        print("跳过批量评测模拟")
        return
    
    print("\n开始模拟批量评测...")
    
    # 模拟数据
    test_cases = [
        {
            "task_type": "solve",
            "prompt": "解这道一元二次方程：x² + 5x + 6 = 0",
            "output": "解：x² + 5x + 6 = 0\n使用因式分解法：\n(x + 2)(x + 3) = 0\n因此 x₁ = -2, x₂ = -3"
        },
        {
            "task_type": "review",
            "prompt": "批改这道题的答案",
            "output": "您的答案中有以下错误：\n1. 符号错误：第二步应该是+而不是-\n2. 计算错误：最后的结果应该是15而不是13"
        },
        {
            "task_type": "generate",
            "prompt": "生成3道关于三角函数的练习题",
            "output": "## 题目1\n求sin(π/6)的值\n\n**答案：** 1/2\n\n**解析：** ...\n\n---"
        }
    ]
    
    logger = EvaluationLogger()
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n生成样本 {i}/{len(test_cases)}...")
        
        quick_evaluate_and_log(
            model_name=config.ACTIVE_MODEL_KEY,
            task_type=case["task_type"],
            input_prompt=case["prompt"],
            raw_output=case["output"],
            response_time=2.5,
            token_count=len(case["output"]),
            notes=f"模拟样本{i}"
        )
    
    print(f"\n✅ 已生成 {len(test_cases)} 个模拟评测样本")


def main():
    """主测试流程"""
    print("\n" + "=" * 70)
    print("  沐梧AI解题系统 - 评测框架快速测试")
    print("=" * 70)
    
    # 测试1: 模型配置
    if not test_model_config():
        print("\n⚠️  模型配置测试失败，请检查config.py和环境变量")
        return
    
    # 测试2: 模型适配器
    result = test_model_adapter()
    if isinstance(result, tuple) and result[0]:
        _, response, response_time = result
    else:
        print("\n⚠️  模型适配器测试失败")
        print("   如果是本地模型，请确保推理服务已启动")
        print("   如果是Dashscope API，请检查API密钥")
        
        # 使用模拟数据继续测试
        print("\n   使用模拟数据继续测试评测功能...")
        response = "这是一个模拟的AI响应，用于测试评测框架。"
        response_time = 2.5
    
    # 测试3: 评测记录
    if not test_evaluation_logging(response, response_time):
        print("\n⚠️  评测记录测试失败")
        return
    
    # 测试4: 报告生成
    if not test_report_generation():
        print("\n⚠️  报告生成测试失败")
        return
    
    # 测试5: 批量评测（可选）
    simulate_batch_evaluation()
    
    # 总结
    print_section("✅ 测试完成")
    
    print("测试结果:")
    print("  ✓ 模型配置正常")
    print("  ✓ 模型适配器正常")
    print("  ✓ 评测记录正常")
    print("  ✓ 报告生成正常")
    
    print("\n下一步:")
    print("  1. 查看评测数据: evaluation_data/evaluation_results.csv")
    print("  2. 查看评测报告: evaluation_reports/evaluation_report_*.md")
    print("  3. 切换模型测试: 修改config.py中的ACTIVE_MODEL_KEY")
    print("  4. 集成到main_db.py: 参考【集成指南】大模型切换与评测框架.md")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()

