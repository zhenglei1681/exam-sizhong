"""
表单填写模块

负责填写表单字段、点击按钮、触发提交
"""
from typing import Optional
import logging

try:
    from playwright.async_api import Page
except ImportError:
    Page = None

logger = logging.getLogger(__name__)


class FormFiller:
    """表单填写工具类"""

    def __init__(self, page: Page):
        """
        初始化表单填写工具

        Args:
            page: Playwright 页面对象
        """
        if Page is None:
            raise ImportError("请先安装 playwright: pip install playwright")

        self.page = page

    async def fill_input(self, selector: str, value: str, delay: int = 100) -> None:
        """
        填写输入框

        Args:
            selector: 输入框的 CSS 选择器
            value: 要填写的值
            delay: 每次输入的延迟（毫秒），模拟人工输入
        """
        logger.debug(f"填写输入框 {selector}: {value}")
        await self.page.fill(selector, str(value), delay=delay)

    async def type_input(self, selector: str, text: str, delay: int = 50) -> None:
        """
        模拟键盘输入

        Args:
            selector: 输入框的 CSS 选择器
            text: 要输入的文本
            delay: 每次按键的延迟（毫秒）
        """
        logger.debug(f"键盘输入 {selector}: {text}")
        await self.page.type(selector, text, delay=delay)

    async def clear_input(self, selector: str) -> None:
        """
        清空输入框

        Args:
            selector: 输入框的 CSS 选择器
        """
        logger.debug(f"清空输入框 {selector}")
        await self.page.fill(selector, "")

    async def click_button(self, selector: str) -> None:
        """
        点击按钮

        Args:
            selector: 按钮的 CSS 选择器
        """
        logger.debug(f"点击按钮 {selector}")
        await self.page.click(selector)

    async def submit_form(self, selector: str = "form") -> None:
        """
        提交表单

        Args:
            selector: 表单的 CSS 选择器
        """
        logger.debug(f"提交表单 {selector}")
        await self.page.locator(selector).evaluate("form => form.submit()")

    async def select_option(
        self,
        selector: str,
        value: str = None,
        label: str = None,
        index: int = None
    ) -> None:
        """
        选择下拉框选项

        Args:
            selector: 下拉框的 CSS 选择器
            value: 选项值
            label: 选项标签
            index: 选项索引
        """
        logger.debug(f"选择下拉框 {selector}: value={value}, label={label}, index={index}")
        await self.page.select_option(selector, value=value, label=label, index=index)

    async def check_checkbox(self, selector: str, checked: bool = True) -> None:
        """
        设置复选框状态

        Args:
            selector: 复选框的 CSS 选择器
            checked: 是否选中
        """
        logger.debug(f"设置复选框 {selector}: checked={checked}")
        await self.page.set_checked(selector, checked)

    async def press_key(self, selector: str, key: str) -> None:
        """
        按下键盘按键

        Args:
            selector: 元素选择器（为 None 则在整个页面按）
            key: 按键名称（如 Enter, Tab, Escape 等）
        """
        if selector:
            await self.page.locator(selector).press(key)
        else:
            await self.page.keyboard.press(key)
        logger.debug(f"按下按键: {key}")

    async def submit_score(self, selector: str, score: float) -> None:
        """
        提交分数（填写并回车）

        Args:
            selector: 得分输入框的 CSS 选择器
            score: 分数
        """
        await self.fill_input(selector, score)
        await self.press_key(selector, "Enter")
        logger.info(f"已提交分数: {score}")
