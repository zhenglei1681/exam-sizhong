"""
提示词模板模块

管理判卷相关的提示词模板
"""


class PromptTemplates:
    """提示词模板类"""

    # 默认判卷提示词模板
    DEFAULT_JUDGE_TEMPLATE = """你是一个阅卷专家，请根据以下信息判阅学生的答案。

题目：{question}
标准答案：{standard_answer}
学生答案：{student_answer}
满分：{max_points}

请严格按照以下要求判阅：
1. 仔细比较学生答案与标准答案
2. 根据答案的完整性和正确性给分
3. 给分范围：0-{max_points}分
4. 必须给出简要评语说明给分理由

请以JSON格式返回结果，格式如下：
{{"score": 实际得分, "comment": "评语"}}
"""

    # 严格判卷提示词
    STRICT_JUDGE_TEMPLATE = """你是一个严格的阅卷专家，请根据以下信息判阅学生的答案。

题目：{question}
标准答案：{standard_answer}
学生答案：{student_answer}
满分：{max_points}

判阅标准：
1. 答案必须与标准答案高度一致才能给满分
2. 部分正确可以给予部分分数
3. 答案完全错误或无关则给0分

请以JSON格式返回结果，格式如下：
{{"score": 实际得分, "comment": "评语"}}
"""

    # 宽松判卷提示词
    LENIENT_JUDGE_TEMPLATE = """你是一个宽容的阅卷专家，请根据以下信息判阅学生的答案。

题目：{question}
标准答案：{standard_answer}
学生答案：{student_answer}
满分：{max_points}

判阅标准：
1. 只要学生答案包含标准答案的核心要点，就可以给高分
2. 表达方式不同但意思正确的，应该给予认可
3. 即使有小的错误，也可以给予大部分分数

请以JSON格式返回结果，格式如下：
{{"score": 实际得分, "comment": "评语"}}
"""

    @staticmethod
    def get_template(template_type: str = "default") -> str:
        """
        获取指定类型的提示词模板

        Args:
            template_type: 模板类型 (default/strict/lenient)

        Returns:
            提示词模板字符串
        """
        templates = {
            "default": PromptTemplates.DEFAULT_JUDGE_TEMPLATE,
            "strict": PromptTemplates.STRICT_JUDGE_TEMPLATE,
            "lenient": PromptTemplates.LENIENT_JUDGE_TEMPLATE
        }
        return templates.get(template_type, PromptTemplates.DEFAULT_JUDGE_TEMPLATE)

    @staticmethod
    def format_template(template: str, **kwargs) -> str:
        """
        格式化提示词模板

        Args:
            template: 模板字符串
            **kwargs: 格式化参数

        Returns:
            格式化后的提示词
        """
        return template.format(**kwargs)
