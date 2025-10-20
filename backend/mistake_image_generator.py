"""
错题图片生成器 - 测试工具
用于生成包含题目和错误解析的错题图片（JPG格式）
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import textwrap
from datetime import datetime
import random

# 输出目录
OUTPUT_DIR = Path(r"D:\360安全浏览器下载\题目\错题样本")

# 确保输出目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 题库数据
QUESTION_BANK = {
    "数学": {
        "简单": [
            {
                "question": "计算：3 + 5 × 2 = ?",
                "wrong_answer": "16",
                "correct_answer": "13",
                "analysis": "错误原因：未按照运算顺序计算。\n\n正确解法：\n先算乘法：5 × 2 = 10\n再算加法：3 + 10 = 13\n\n记住：四则运算中，先算乘除，后算加减。"
            },
            {
                "question": "求方程 2x + 3 = 7 的解",
                "wrong_answer": "x = 1",
                "correct_answer": "x = 2",
                "analysis": "错误原因：移项时符号处理错误。\n\n正确解法：\n2x + 3 = 7\n2x = 7 - 3\n2x = 4\nx = 2\n\n注意：移项要改变符号！"
            },
            {
                "question": "计算：(-3) × (-2) = ?",
                "wrong_answer": "-6",
                "correct_answer": "6",
                "analysis": "错误原因：负负得正的规则没掌握。\n\n正确解法：\n(-3) × (-2) = 6\n\n记住口诀：\n同号得正，异号得负。"
            }
        ],
        "中等": [
            {
                "question": "求函数 f(x) = x² + 2x + 1 的最小值及对应的x值",
                "wrong_answer": "最小值为1，x = 0",
                "correct_answer": "最小值为0，x = -1",
                "analysis": "错误原因：未正确配方。\n\n正确解法：\nf(x) = x² + 2x + 1\n     = (x + 1)²\n     ≥ 0\n\n当 x + 1 = 0，即 x = -1 时，\nf(x)取得最小值 0。\n\n知识点：二次函数配方法求最值。"
            },
            {
                "question": "已知等差数列{aₙ}中，a₁=2，d=3，求a₅",
                "wrong_answer": "a₅ = 15",
                "correct_answer": "a₅ = 14",
                "analysis": "错误原因：公式使用错误。\n\n正确解法：\n等差数列通项公式：\naₙ = a₁ + (n-1)d\n\na₅ = a₁ + (5-1)×3\n   = 2 + 4×3\n   = 2 + 12\n   = 14\n\n注意：是(n-1)d，不是nd！"
            }
        ],
        "困难": [
            {
                "question": "求极限：lim(x→0) [sin(x) / x]",
                "wrong_answer": "0/0，极限不存在",
                "correct_answer": "1",
                "analysis": "错误原因：不了解重要极限。\n\n这是一个重要极限：\nlim(x→0) [sin(x) / x] = 1\n\n证明思路：\n利用夹逼定理，在单位圆中：\ncos(x) < sin(x)/x < 1 (当0 < x < π/2)\n\n由夹逼定理得：\nlim(x→0) [sin(x) / x] = 1\n\n这个结论需要记住！"
            },
            {
                "question": "求不定积分：∫x·e^x dx",
                "wrong_answer": "e^x + C",
                "correct_answer": "(x-1)·e^x + C",
                "analysis": "错误原因：未使用分部积分法。\n\n正确解法（分部积分）：\n令 u = x, dv = e^x dx\n则 du = dx, v = e^x\n\n∫x·e^x dx = x·e^x - ∫e^x dx\n           = x·e^x - e^x + C\n           = (x-1)·e^x + C\n\n分部积分公式：\n∫u dv = uv - ∫v du"
            }
        ]
    },
    "物理": {
        "简单": [
            {
                "question": "一个物体做匀速直线运动，速度为5m/s，求10秒后的位移",
                "wrong_answer": "50米",
                "correct_answer": "50米",
                "analysis": "回答正确！\n\n解法：\n匀速直线运动位移公式：\ns = v·t\n\n代入数据：\ns = 5 m/s × 10 s = 50 m\n\n继续保持！"
            },
            {
                "question": "重力加速度g约等于多少？（取整数）",
                "wrong_answer": "9.8 m/s²",
                "correct_answer": "10 m/s²（取整数）",
                "analysis": "题目要求取整数！\n\n精确值：g = 9.8 m/s²\n取整数：g ≈ 10 m/s²\n\n做题时要注意：\n看清题目要求！"
            }
        ],
        "中等": [
            {
                "question": "一个物体从10m高处自由落下，不计空气阻力，落地时速度多大？(g=10m/s²)",
                "wrong_answer": "v = 10 m/s",
                "correct_answer": "v = 10√2 m/s ≈ 14.1 m/s",
                "analysis": "错误原因：公式使用错误。\n\n正确解法：\n自由落体运动，使用公式：\nv² = 2gh\n\n代入数据：\nv² = 2 × 10 × 10 = 200\nv = √200 = 10√2 ≈ 14.1 m/s\n\n常用公式：\n1. v = gt\n2. h = ½gt²\n3. v² = 2gh"
            },
            {
                "question": "质量为2kg的物体受到10N的力，求加速度（不计摩擦）",
                "wrong_answer": "a = 20 m/s²",
                "correct_answer": "a = 5 m/s²",
                "analysis": "错误原因：公式 F=ma 使用错误。\n\n正确解法：\n牛顿第二定律：F = ma\n\na = F / m = 10N / 2kg = 5 m/s²\n\n注意：\n加速度 = 力 ÷ 质量\n不是 力 × 质量！"
            }
        ],
        "困难": [
            {
                "question": "光在真空中的速度是多少？单位是什么？",
                "wrong_answer": "3×10^8 m/s",
                "correct_answer": "c = 3×10^8 m/s（准确值：2.998×10^8 m/s）",
                "analysis": "回答基本正确！\n\n光速是自然界中最快的速度：\nc = 3×10^8 m/s\n\n精确值：\nc = 299,792,458 m/s\n≈ 3.0×10^8 m/s\n\n这是一个重要的物理常数！\n\n相关知识：\n爱因斯坦相对论指出，\n任何物体的速度都不能超过光速。"
            }
        ]
    },
    "化学": {
        "简单": [
            {
                "question": "写出水的化学式",
                "wrong_answer": "HO",
                "correct_answer": "H₂O",
                "analysis": "错误原因：原子个数标注错误。\n\n水分子由2个氢原子和1个氧原子组成。\n\n正确写法：H₂O\n错误写法：HO（少了一个氢原子）\n\n记住：\nH - 氢元素\nO - 氧元素\n₂ - 表示2个原子"
            },
            {
                "question": "酸的pH值范围是多少？",
                "wrong_answer": "pH > 7",
                "correct_answer": "pH < 7",
                "analysis": "错误原因：酸碱性判断混淆。\n\n正确记忆：\npH < 7  →  酸性\npH = 7  →  中性\npH > 7  →  碱性\n\npH值越小，酸性越强。\npH值越大，碱性越强。"
            }
        ],
        "中等": [
            {
                "question": "配平方程式：__ Fe + __ O₂ → __ Fe₃O₄",
                "wrong_answer": "1 Fe + 1 O₂ → 1 Fe₃O₄",
                "correct_answer": "3 Fe + 2 O₂ → Fe₃O₄",
                "analysis": "错误原因：配平不正确。\n\n正确配平过程：\n1. Fe₃O₄中有3个Fe，4个O\n2. 左边Fe系数为3\n3. 右边有4个O，O₂系数为2\n\n最终：3 Fe + 2 O₂ → Fe₃O₄\n\n配平技巧：\n先配奇数，后配偶数。\n从复杂分子开始配。"
            }
        ],
        "困难": [
            {
                "question": "写出乙醇的结构式",
                "wrong_answer": "CH₃OH",
                "correct_answer": "CH₃CH₂OH 或 C₂H₅OH",
                "analysis": "错误原因：把乙醇和甲醇混淆了。\n\n甲醇：CH₃OH\n乙醇：CH₃CH₂OH\n\n记忆方法：\n甲 - 一个碳 - CH₃OH\n乙 - 两个碳 - C₂H₅OH\n\n乙醇俗称酒精，\n是日常生活中常见的消毒剂。"
            }
        ]
    },
    "英语": {
        "简单": [
            {
                "question": "翻译：I am a student.",
                "wrong_answer": "我是学生的。",
                "correct_answer": "我是一名学生。",
                "analysis": "翻译基本正确，但不够地道。\n\n原句：I am a student.\n直译：我是一名学生。\n\n'a student' 表示'一名学生'，\n不需要加'的'字。\n\n翻译要点：\n1. 理解原意\n2. 符合中文习惯\n3. 简洁明了"
            }
        ],
        "中等": [
            {
                "question": "选择正确的时态：He _____ (go) to school every day.\nA. go  B. goes  C. going  D. went",
                "wrong_answer": "A. go",
                "correct_answer": "B. goes",
                "analysis": "错误原因：主谓不一致。\n\n正确分析：\n1. 句子表达习惯动作，用一般现在时\n2. 主语是第三人称单数 (He)\n3. 动词要加 -s\n\n正确答案：He goes to school every day.\n\n记住：\n第三人称单数（he/she/it）\n+ 一般现在时\n→ 动词加 -s/-es"
            }
        ],
        "困难": [
            {
                "question": "翻译并解释：The early bird catches the worm.",
                "wrong_answer": "早起的鸟儿抓虫子。",
                "correct_answer": "早起的鸟儿有虫吃。（谚语：早起的人能抓住机会）",
                "analysis": "翻译字面意思正确，但未理解其含义。\n\n这是一句英语谚语：\nThe early bird catches the worm.\n\n字面意思：\n早起的鸟儿能抓到虫子。\n\n深层含义：\n1. 勤奋的人能获得更多机会\n2. 先下手为强\n3. 时间就是金钱\n\n对应中文谚语：\n'早起的鸟儿有虫吃'\n'笨鸟先飞'\n'一日之计在于晨'\n\n英语学习要理解文化内涵！"
            }
        ]
    }
}

# 颜色配置
COLORS = {
    "bg": (255, 255, 255),  # 白色背景
    "title": (220, 240, 255),  # 淡蓝色标题背景
    "question_bg": (250, 250, 250),  # 浅灰色题目背景
    "wrong_bg": (255, 235, 235),  # 浅红色错误背景
    "correct_bg": (235, 255, 235),  # 浅绿色正确背景
    "analysis_bg": (255, 250, 235),  # 浅黄色分析背景
    "border": (200, 200, 200),  # 灰色边框
    "text": (50, 50, 50),  # 深灰色文字
    "title_text": (70, 100, 150),  # 蓝色标题文字
    "wrong_text": (200, 50, 50),  # 红色错误文字
    "correct_text": (50, 150, 50),  # 绿色正确文字
}


def wrap_text(text, font, max_width):
    """
    文本自动换行
    """
    lines = []
    for paragraph in text.split('\n'):
        if not paragraph:
            lines.append('')
            continue
        
        # 估算每行字符数
        avg_char_width = font.getbbox('测')[2]
        chars_per_line = max(1, int(max_width / avg_char_width))
        
        # 使用textwrap处理
        wrapped = textwrap.wrap(paragraph, width=chars_per_line)
        if wrapped:
            lines.extend(wrapped)
        else:
            lines.append('')
    
    return lines


def calculate_text_height(text, font, max_width):
    """
    计算文本所需高度
    """
    lines = wrap_text(text, font, max_width)
    line_height = font.getbbox('测试')[3] + 8
    return len(lines) * line_height + 20


def draw_rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    """
    绘制圆角矩形
    """
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill, outline=outline, width=width)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill, outline=outline, width=width)
    draw.ellipse([x1, y1, x1 + radius * 2, y1 + radius * 2], fill=fill, outline=outline, width=width)
    draw.ellipse([x2 - radius * 2, y1, x2, y1 + radius * 2], fill=fill, outline=outline, width=width)
    draw.ellipse([x1, y2 - radius * 2, x1 + radius * 2, y2], fill=fill, outline=outline, width=width)
    draw.ellipse([x2 - radius * 2, y2 - radius * 2, x2, y2], fill=fill, outline=outline, width=width)


def draw_text_block(draw, text, font, x, y, max_width, color):
    """
    绘制文本块（支持换行）
    """
    lines = wrap_text(text, font, max_width)
    line_height = font.getbbox('测试')[3] + 8
    
    current_y = y
    for line in lines:
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += line_height
    
    return current_y


def generate_mistake_image(subject, difficulty, question_data, output_path):
    """
    生成错题图片
    
    Args:
        subject: 科目
        difficulty: 难度
        question_data: 题目数据字典
        output_path: 输出路径
    """
    # 图片尺寸
    width = 800
    margin = 40
    content_width = width - 2 * margin
    
    # 加载字体（尝试使用系统字体）
    try:
        title_font = ImageFont.truetype("msyh.ttc", 24)  # 微软雅黑
        subtitle_font = ImageFont.truetype("msyh.ttc", 18)
        content_font = ImageFont.truetype("msyh.ttc", 16)
    except:
        # 如果加载失败，使用默认字体
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        content_font = ImageFont.load_default()
    
    # 计算所需高度
    question_height = calculate_text_height(question_data['question'], content_font, content_width - 40)
    wrong_height = calculate_text_height(f"你的答案：{question_data['wrong_answer']}", content_font, content_width - 40)
    correct_height = calculate_text_height(f"正确答案：{question_data['correct_answer']}", content_font, content_width - 40)
    analysis_height = calculate_text_height(question_data['analysis'], content_font, content_width - 40)
    
    total_height = (
        100 +  # 标题区域
        question_height +  # 题目区域
        wrong_height +  # 错误答案区域
        correct_height +  # 正确答案区域
        analysis_height +  # 分析区域
        100  # 底部空白
    )
    
    # 创建图片
    img = Image.new('RGB', (width, total_height), COLORS['bg'])
    draw = ImageDraw.Draw(img)
    
    current_y = margin
    
    # 1. 标题区域
    draw_rounded_rectangle(
        draw,
        [margin, current_y, width - margin, current_y + 70],
        radius=10,
        fill=COLORS['title'],
        outline=COLORS['border'],
        width=2
    )
    
    # 绘制标题文字
    title_text = "❌ 错题记录"
    draw.text((margin + 20, current_y + 15), title_text, font=title_font, fill=COLORS['title_text'])
    
    # 科目和难度标签
    info_text = f"科目：{subject}  |  难度：{difficulty}"
    draw.text((margin + 20, current_y + 45), info_text, font=subtitle_font, fill=COLORS['text'])
    
    current_y += 90
    
    # 2. 题目区域
    draw_rounded_rectangle(
        draw,
        [margin, current_y, width - margin, current_y + question_height],
        radius=8,
        fill=COLORS['question_bg'],
        outline=COLORS['border'],
        width=1
    )
    
    draw.text((margin + 20, current_y + 10), "📝 题目：", font=subtitle_font, fill=COLORS['text'])
    current_y = draw_text_block(
        draw,
        question_data['question'],
        content_font,
        margin + 20,
        current_y + 40,
        content_width - 40,
        COLORS['text']
    )
    current_y += 20
    
    # 3. 错误答案区域
    draw_rounded_rectangle(
        draw,
        [margin, current_y, width - margin, current_y + wrong_height],
        radius=8,
        fill=COLORS['wrong_bg'],
        outline=COLORS['border'],
        width=1
    )
    
    current_y = draw_text_block(
        draw,
        f"❌ 你的答案：{question_data['wrong_answer']}",
        content_font,
        margin + 20,
        current_y + 15,
        content_width - 40,
        COLORS['wrong_text']
    )
    current_y += 20
    
    # 4. 正确答案区域
    draw_rounded_rectangle(
        draw,
        [margin, current_y, width - margin, current_y + correct_height],
        radius=8,
        fill=COLORS['correct_bg'],
        outline=COLORS['border'],
        width=1
    )
    
    current_y = draw_text_block(
        draw,
        f"✅ 正确答案：{question_data['correct_answer']}",
        content_font,
        margin + 20,
        current_y + 15,
        content_width - 40,
        COLORS['correct_text']
    )
    current_y += 20
    
    # 5. 分析区域
    draw_rounded_rectangle(
        draw,
        [margin, current_y, width - margin, current_y + analysis_height],
        radius=8,
        fill=COLORS['analysis_bg'],
        outline=COLORS['border'],
        width=1
    )
    
    draw.text((margin + 20, current_y + 10), "💡 详细分析：", font=subtitle_font, fill=COLORS['text'])
    draw_text_block(
        draw,
        question_data['analysis'],
        content_font,
        margin + 20,
        current_y + 40,
        content_width - 40,
        COLORS['text']
    )
    
    # 保存图片
    img.save(output_path, 'JPEG', quality=95)
    print(f"✅ 已生成：{output_path}")


def interactive_generate():
    """
    交互式生成错题图片
    """
    print("\n" + "=" * 60)
    print("  🎓 错题图片生成器")
    print("=" * 60)
    print(f"\n📁 输出目录：{OUTPUT_DIR}\n")
    
    while True:
        # 选择科目
        print("\n📚 可用科目：")
        subjects = list(QUESTION_BANK.keys())
        for i, subject in enumerate(subjects, 1):
            print(f"  {i}. {subject}")
        print("  0. 退出程序")
        
        try:
            choice = int(input("\n请选择科目（输入数字）："))
            if choice == 0:
                print("\n👋 再见！")
                break
            if choice < 1 or choice > len(subjects):
                print("❌ 无效选择，请重试")
                continue
            
            subject = subjects[choice - 1]
            
            # 选择难度
            print(f"\n📊 {subject} - 可用难度：")
            difficulties = list(QUESTION_BANK[subject].keys())
            for i, diff in enumerate(difficulties, 1):
                count = len(QUESTION_BANK[subject][diff])
                print(f"  {i}. {diff} (共{count}题)")
            
            diff_choice = int(input("\n请选择难度（输入数字）："))
            if diff_choice < 1 or diff_choice > len(difficulties):
                print("❌ 无效选择，请重试")
                continue
            
            difficulty = difficulties[diff_choice - 1]
            
            # 选择题目
            questions = QUESTION_BANK[subject][difficulty]
            print(f"\n📝 {subject} - {difficulty} - 可用题目：")
            for i, q in enumerate(questions, 1):
                preview = q['question'][:30] + "..." if len(q['question']) > 30 else q['question']
                print(f"  {i}. {preview}")
            print("  0. 随机选择")
            
            q_choice = int(input("\n请选择题目（输入数字）："))
            if q_choice == 0:
                question_data = random.choice(questions)
            elif q_choice < 1 or q_choice > len(questions):
                print("❌ 无效选择，请重试")
                continue
            else:
                question_data = questions[q_choice - 1]
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"错题_{subject}_{difficulty}_{timestamp}.jpg"
            output_path = OUTPUT_DIR / filename
            
            # 生成图片
            print(f"\n🎨 正在生成图片...")
            generate_mistake_image(subject, difficulty, question_data, output_path)
            
            # 询问是否继续
            continue_choice = input("\n是否继续生成？(y/n): ").lower()
            if continue_choice != 'y':
                print("\n👋 再见！")
                break
                
        except ValueError:
            print("❌ 请输入有效的数字")
        except KeyboardInterrupt:
            print("\n\n👋 程序已中断")
            break
        except Exception as e:
            print(f"\n❌ 发生错误：{e}")


if __name__ == "__main__":
    interactive_generate()

