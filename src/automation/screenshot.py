"""
截图功能模块

负责截取页面或元素的图片
"""
import os
from typing import Optional
from datetime import datetime
import logging

try:
    from playwright.async_api import Page
except ImportError:
    Page = None

logger = logging.getLogger(__name__)


class Screenshot:
    """截图工具类"""

    def __init__(
        self,
        page: Page,
        save_dir: str = "screenshots",
        auto_save: bool = True
    ):
        """
        初始化截图工具

        Args:
            page: Playwright 页面对象
            save_dir: 截图保存目录
            auto_save: 是否自动保存截图
        """
        if Page is None:
            raise ImportError("请先安装 playwright: pip install playwright")

        self.page = page
        self.save_dir = save_dir
        self.auto_save = auto_save

        # 确保保存目录存在
        if auto_save:
            os.makedirs(save_dir, exist_ok=True)

    async def capture_page(self, full_page: bool = True) -> bytes:
        """
        截取整个页面

        Args:
            full_page: 是否截取完整页面（包括滚动区域）

        Returns:
            截图数据（bytes）
        """
        screenshot = await self.page.screenshot(full_page=full_page)
        return screenshot

    async def capture_element(self, selector: str) -> bytes:
        """
        截取指定元素

        Args:
            selector: 元素的 CSS 选择器

        Returns:
            截图数据（bytes）
        """
        element = await self.page.query_selector(selector)
        if not element:
            raise ValueError(f"未找到元素: {selector}")

        screenshot = await element.screenshot()
        return screenshot

    async def capture_region(self, x: int, y: int, width: int, height: int) -> bytes:
        """
        截取指定区域

        Args:
            x: X 坐标
            y: Y 坐标
            width: 宽度
            height: 高度

        Returns:
            截图数据（bytes）
        """
        clip = {"x": x, "y": y, "width": width, "height": height}
        screenshot = await self.page.screenshot(clip=clip)
        return screenshot

    async def capture_and_save(
        self,
        selector: str = None,
        filename: str = None,
        full_page: bool = True
    ) -> str:
        """
        截取并保存图片

        Args:
            selector: 元素选择器（如果指定则截取该元素）
            filename: 文件名（不指定则自动生成）
            full_page: 是否截取完整页面

        Returns:
            保存的文件路径
        """
        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"

        filepath = os.path.join(self.save_dir, filename)

        # 截图
        if selector:
            screenshot = await self.capture_element(selector)
        else:
            screenshot = await self.capture_page(full_page=full_page)

        # 保存
        with open(filepath, 'wb') as f:
            f.write(screenshot)

        logger.info(f"截图已保存: {filepath}")
        return filepath

    def set_save_dir(self, dir: str):
        """
        设置截图保存目录

        Args:
            dir: 保存目录路径
        """
        self.save_dir = dir
        if self.auto_save:
            os.makedirs(dir, exist_ok=True)
