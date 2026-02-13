"""
阅卷系统主程序

自动化识别试卷、AI 判卷、填写分数
"""
import asyncio
import sys
import os
import time
import logging
from io import BytesIO
from typing import Optional

from PIL import Image

from src.utils.config_loader import ConfigLoader
from src.utils.logger import Logger
from src.auth.license_manager import LicenseManager
from src.ai.ai_client import AIClient
from src.ai.prompt_templates import PromptTemplates
from src.ocr.ocr_engine import OCREngine
from src.grading.ai_judge import AIJudge
from src.grading.score_calculator import ScoreCalculator
from src.automation.browser_controller import BrowserController
from src.automation.screenshot import Screenshot
from src.automation.form_filler import FormFiller


# 设置项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)

# 初始化日志
logger = Logger.setup("grading_system", log_dir="logs")


class GradingSystem:
    """阅卷系统主类"""

    def __init__(self, config: dict):
        """
        初始化阅卷系统

        Args:
            config: 配置字典
        """
        self.config = config

        # 初始化授权管理器
        self.license_manager = None
        if config["settings"]["license"]["enabled"]:
            self.license_manager = LicenseManager(config["settings"])

        # 初始化 AI 客户端
        self.ai_client = AIClient(config["settings"]["ai"])

        # 初始化 OCR 引擎
        ocr_config = config["settings"]["get("ocr", {}")"]
        self.ocr = OCREngine(ocr_config)

        # 初始化判卷器和评分计算器
        questions = config["questions"]["questions"]
        template = config["questions"].get("prompt_template") or PromptTemplates.get_template()
        self.judge = AIJudge(self.ai_client, template)
        passing_score = config["questions"].get("scoring", {}).get("passing_score", 60)
        self.calculator = ScoreCalculator(questions, passing_score)

        # 自动化组件（延迟初始化）
        self.browser: Optional[BrowserController] = None
        self.screenshot: Optional[Screenshot] = None
        self.form_filler: Optional[FormFiller] = None

    async def start(self):
        """启动系统"""
        # 授权验证
        if self.license_manager and not self.license_manager.is_authorized():
            license_code = input("请输入授权码: ")
            if not self.license_manager.verify_license(license_code):
                logger.error("授权验证失败！")
                sys.exit(1)
            if not self.license_manager.save_license(license_code):
                logger.error("授权保存失败！")
                sys.exit(1)
            logger.info("授权验证成功！")

        # 显示授权信息
        if self.license_manager:
            info = self.license_manager.get_license_info()
            logger.info(f"授权状态: {'已授权' if info['authorized'] else '未授权'}")
            if info.get("authorized"):
                logger.info(f"有效期至: {info.get('valid_until')}")

        # 初始化浏览器
        self.browser = BrowserController(self.config["browser"])
        await self.browser.start()

        page = await self.browser.get_page()

        # 初始化截图和表单填写工具
        screenshot_dir = self.config["settings"]["app"].get("screenshot_dir", "screenshots")
        self.screenshot = Screenshot(page, save_dir=screenshot_dir)
        self.form_filler = FormFiller(page)

        # 导航到目标页面
        url = self.config["browser"]["target"]["url"]
        await self.browser.navigate(url)
        logger.info(f"已打开页面: {url}")

    async def process_exam(self) -> bool:
        """
        处理一张试卷

        Returns:
            是否成功处理
        """
        browser_config = self.config["browser"]
        selectors = browser_config.get("selectors", {})
        automation_config = browser_config.get("automation", {})

        try:
            # 等待试卷图片加载
            image_selector = selectors.get("exam_image", "#exam-container img")
            logger.info("等待试卷图片加载...")

            timeout = 30000  # 30秒超时
            await self.browser.wait_for_element(image_selector, timeout=timeout)

            # 截取试卷图片
            logger.info("截取试卷图片...")
            image_data = await self.screenshot.capture_element(image_selector)

            # OCR 识别
            logger.info("识别试卷文字...")
            image = Image.open(BytesIO(image_data))
            ocr_results = self.ocr.recognize(image)

            # 拼接识别文本
            recognized_text = "\n".join([item["text"] for item in ocr_results])
            logger.info(f"识别到文字: {len(recognized_text)} 字符")

            # AI 判卷
            logger.info("AI 判卷中...")
            questions = self.config["questions"]["questions"]

            judge_results = []
            for question in questions:
                result = self.judge.judge(question, recognized_text)
                judge_results.append(result)
                logger.debug(f"题目 {question.get('id')}: {result.get('score')}/{question.get('points')} 分")

            # 计算总分
            report = self.calculator.generate_report(judge_results)
            total_score = report["total_score"]

            logger.info(f"判卷完成！得分: {total_score}/{report['max_score']} ({report['percentage']}%)")
            logger.info(f"及格: {'是' if report['passed'] else '否'}")

            # 填写分数
            score_input_selector = selectors.get("score_input", "input[name='score']")
            wait_after_fill = automation_config.get("wait_after_fill", 500)

            await self.form_filler.fill_input(score_input_selector, total_score)
            await asyncio.sleep(wait_after_fill / 1000)  # 转换为秒
            logger.info("分数已填写")

            # 点击下一张
            next_button_selector = selectors.get("next_button", "button.next-exam")
            await self.form_filler.click_button(next_button_selector)
            logger.info("已点击下一张")

            return True

        except Exception as e:
            logger.error(f"处理试卷失败: {e}", exc_info=True)
            return False

    async def run(self, max_exams: int = None):
        """
        运行阅卷系统

        Args:
            max_exams: 最大处理试卷数（None 表示无限）
        """
        processed = 0

        while max_exams is None or processed < max_exams:
            logger.info(f"\n{'=' * 50}")
            logger.info(f"处理第 {processed + 1} 张试卷")
            logger.info(f"{'=' * 50}\n")

            success = await self.process_exam()

            if success:
                processed += 1
            else:
                logger.error("处理失败，停止运行")
                break

            # 等待一段时间再处理下一张
            wait_time = 2
            logger.info(f"等待 {wait_time} 秒后处理下一张...")
            await asyncio.sleep(wait_time)

        logger.info(f"\n处理完成！共处理 {processed} 张试卷")

    async def shutdown(self):
        """关闭系统"""
        if self.browser:
            await self.browser.close()
            logger.info("浏览器已关闭")


async def main():
    """主函数"""
    try:
        # 加载配置
        logger.info("加载配置文件...")
        config_loader = ConfigLoader("config")
        config = config_loader.load_all()

        # 创建系统实例
        system = GradingSystem(config)

        # 启动系统
        await system.start()

        # 运行阅卷
        await system.run()

    except KeyboardInterrupt:
        logger.info("\n用户中断，正在关闭...")
    except Exception as e:
        logger.error(f"系统错误: {e}", exc_info=True)
    finally:
        if 'system' in locals():
            await system.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
