"""
AI 判卷模块

负责构建判卷提示词、调用 AI、解析判卷结果
"""
from typing import Dict, Any, Optional
import logging

from src.ai.ai_client import AIClient
from src.ai.prompt_templates import PromptTemplates


logger = logging.getLogger(__name__)


class AIJudge:
    """AI 判卷器"""

    def __init__(self, ai_client: AIClient, prompt_template: str = None):
        """
        初始化 AI 判卷器

        Args:
            ai_client: AI 客户端实例
            prompt_template: 自定义提示词模板
        """
        self.ai_client = ai_client
        self.prompt_template = prompt_template or PromptTemplates.get_template("default")

    def judge(
        self,
        question: Dict[str, Any],
        student_answer: str
    ) -> Dict[str, Any]:
        """
        判阅一道题

        Args:
            question: 题目字典，包含 text, answer, points 等字段
            student_answer: 学生答案文本

        Returns:
            判卷结果字典，包含 score 和 comment
        """
        prompt = self._build_prompt(question, student_answer)

        try:
            result = self.ai_client.chat_json(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return self._parse_result(result, question["points"])

        except Exception as e:
            logger.error(f"判卷失败: {e}")
            # 失败时返回 0 分
            return {
                "score": 0,
                "comment": f"判卷失败: {str(e)}",
                "question_id": question.get("id")
            }

    def _build_prompt(
        self,
        question: Dict[str, Any],
        student_answer: str
    ) -> str:
        """
        构建判卷提示词

        Args:
            question: 题目字典
            student_answer: 学生答案

        Returns:
            格式化后的提示词
        """
        return self.prompt_template.format(
            question=question.get("text", ""),
            standard_answer=question.get("answer", ""),
            student_answer=student_answer,
            max_points=question.get("points", 10)
        )

    def _parse_result(
        self,
        result: Dict[str, Any],
        max_points: int
    ) -> Dict[str, Any]:
        """
        解析 AI 返回的判卷结果

        Args:
            result: AI 返回的结果
            max_points: 题目满分

        Returns:
            解析后的判卷结果
        """
        # 提取分数
        score = result.get("score", 0)
        comment = result.get("comment", "")

        # 确保分数在合理范围内
        try:
            score = float(score)
        except (ValueError, TypeError):
            score = 0

        score = max(0, min(score, max_points))

        return {
            "score": score,
            "comment": comment
        }

    def set_template(self, template: str):
        """
        设置自定义提示词模板

        Args:
            template: 新的提示词模板
        """
        self.prompt_template = template

    def get_template(self) -> str:
        """
        获取当前提示词模板

        Returns:
            当前提示词模板
        """
        return self.prompt_template
