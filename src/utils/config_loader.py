"""
配置文件加载模块

负责加载和验证 YAML 配置文件
"""
import os
import yaml
from typing import Dict, Any, Optional


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_dir: str = "config"):
        """
        初始化配置加载器

        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = config_dir
        self._settings: Optional[Dict[str, Any]] = None
        self._questions: Optional[Dict[str, Any]] = None
        self._browser: Optional[Dict[str, Any]] = None

    def load_all(self) -> Dict[str, Any]:
        """
        加载所有配置文件

        Returns:
            包含所有配置的字典
        """
        self._settings = self._load_yaml("settings.yaml")
        self._questions = self._load_yaml("questions.yaml")
        self._browser = self._load_yaml("browser.yaml")

        return {
            "settings": self._settings,
            "questions": self._questions,
            "browser": self._browser
        }

    def load_settings(self) -> Dict[str, Any]:
        """加载主配置文件"""
        if self._settings is None:
            self._settings = self._load_yaml("settings.yaml")
        return self._settings

    def load_questions(self) -> Dict[str, Any]:
        """加载题目配置文件"""
        if self._questions is None:
            self._questions = self._load_yaml("questions.yaml")
        return self._questions

    def load_browser(self) -> Dict[str, Any]:
        """加载浏览器配置文件"""
        if self._browser is None:
            self._browser = self._load_yaml("browser.yaml")
        return self._browser

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """
        加载 YAML 文件

        Args:
            filename: 配置文件名

        Returns:
            配置字典
        """
        path = os.path.join(self.config_dir, filename)

        if not os.path.exists(path):
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    @property
    def settings(self) -> Dict[str, Any]:
        """获取主配置"""
        if self._settings is None:
            self.load_settings()
        return self._settings

    @property
    def questions(self) -> Dict[str, Any]:
        """获取题目配置"""
        if self._questions is None:
            self.load_questions()
        return self._questions

    @property
    def browser(self) -> Dict[str, Any]:
        """获取浏览器配置"""
        if self._browser is None:
            self.load_browser()
        return self._browser
