"""
浏览器控制器模块

负责启动/关闭浏览器、页面导航、元素等待
"""
import asyncio
from typing import Dict, Any, Optional
import logging

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserType
except ImportError:
    async_playwright = None

logger = logging.getLogger(__name__)


class BrowserController:
    """浏览器控制器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化浏览器控制器

        Args:
            config: 浏览器配置字典
        """
        if async_playwright is None:
            raise ImportError("请先安装 playwright: pip install playwright")

        self.browser_config = config.get("browser", {})
        self.headless = self.browser_config.get("headless", False)
        self.viewport = self.browser_config.get("viewport", {"width": 1920, "height": 1080})
        self.default_timeout = self.browser_config.get("timeout", 30000)

        self._playwright: Optional[Any] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None

    async def start(self) -> Page:
        """
        启动浏览器

        Returns:
            浏览器页面对象
        """
        self._playwright = await async_playwright().start()

        # 启动浏览器（使用 chromium）
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless
        )

        # 创建新页面
        self._page = await self._browser.new_page(
            viewport=self.viewport
        )

        # 设置默认超时
        self._page.set_default_timeout(self.default_timeout)

        logger.info("浏览器启动成功")
        return self._page

    async def navigate(self, url: str, wait_until: str = "networkidle") -> None:
        """
        导航到指定 URL

        Args:
            url: 目标 URL
            wait_until: 等待条件 (load/domcontentloaded/networkidle)
        """
        if not self._page:
            raise RuntimeError("浏览器未启动，请先调用 start()")

        logger.info(f"导航到: {url}")
        await self._page.goto(url, wait_until=wait_until)

    async def wait_for_element(
        self,
        selector: str,
        timeout: int = None
    ) -> None:
        """
        等待元素出现

        Args:
            selector: CSS 选择器
            timeout: 超时时间（毫秒）
        """
        if not self._page:
            raise RuntimeError("浏览器未启动")

        timeout = timeout or self.default_timeout
        logger.debug(f"等待元素: {selector}")
        await self._page.wait_for_selector(selector, timeout=timeout)

    async def wait_for_navigation(self, timeout: int = None) -> None:
        """
        等待页面导航完成

        Args:
            timeout: 超时时间（毫秒）
        """
        if not self._page:
            raise RuntimeError("浏览器未启动")

        timeout = timeout or self.default_timeout
        await self._page.wait_for_load_state(timeout=timeout)

    async def execute_script(self, script: str) -> Any:
        """
        执行 JavaScript 代码

        Args:
            script: JavaScript 代码

        Returns:
            执行结果
        """
        if not self._page:
            raise RuntimeError("浏览器未启动")

        return await self._page.evaluate(script)

    async def get_page(self) -> Page:
        """
        获取当前页面对象

        Returns:
            页面对象
        """
        if not self._page:
            raise RuntimeError("浏览器未启动，请先调用 start()")

        return self._page

    async def close(self) -> None:
        """关闭浏览器"""
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._page = None
            logger.info("浏览器已关闭")

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    def is_started(self) -> bool:
        """
        检查浏览器是否已启动

        Returns:
            是否已启动
        """
        return self._browser is not None
