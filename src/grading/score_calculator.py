"""
评分计算器模块

负责累加各题得分、计算总分、生成评分报告
"""
from typing import List, Dict, Any


class ScoreCalculator:
    """评分计算器"""

    def __init__(self, questions: List[Dict[str, Any]], passing_score: int = 60):
        """
        初始化评分计算器

        Args:
            questions: 题目列表，每题包含 id, points 等字段
            passing_score: 及格分数
        """
        self.questions = questions
        self.passing_score = passing_score
        self.max_score = sum(q.get("points", 0) for q in questions)

    def calculate_total(self, judge_results: List[Dict[str, Any]]) -> float:
        """
        计算总分

        Args:
            judge_results: 判卷结果列表，每项包含 score 字段

        Returns:
            总分
        """
        return sum(result.get("score", 0) for result in judge_results)

    def generate_report(
        self,
        judge_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成评分报告

        Args:
            judge_results: 判卷结果列表

        Returns:
            包含总分、详细信息等的报告字典
        """
        total_score = self.calculate_total(judge_results)

        # 构建详细报告
        details = []
        for i, (question, result) in enumerate(zip(self.questions, judge_results)):
            details.append({
                "question_id": question.get("id", i + 1),
                "question": question.get("text", ""),
                "max_points": question.get("points", 0),
                "score": result.get("score", 0),
                "comment": result.get("comment", "")
            })

        report = {
            "total_score": total_score,
            "max_score": self.max_score,
            "passing_score": self.passing_score,
            "percentage": round(total_score / self.max_score * 100, 2) if self.max_score > 0 else 0,
            "passed": total_score >= self.passing_score,
            "details": details
        }

        return report

    def is_passed(self, score: float) -> bool:
        """
        判断分数是否及格

        Args:
            score: 分数

        Returns:
            是否及格
        """
        return score >= self.passing_score

    def get_passing_score(self) -> int:
        """
        获取及格分数

        Returns:
            及格分数
        """
        return self.passing_score

    def get_max_score(self) -> int:
        """
        获取满分

        Returns:
            满分
        """
        return self.max_score
