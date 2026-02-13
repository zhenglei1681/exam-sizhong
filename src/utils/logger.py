"""
日志工具模块

配置和管理日志输出
"""
import os
import logging
from typing import Optional


class Logger:
    """日志工具类"""

    _loggers: dict = {}

    @classmethod
    def setup(
        cls,
        name: str,
        log_dir: str = "logs",
        level: int = logging.INFO,
        console_level: int = logging.INFO
    ) -> logging.Logger:
        """
        设置并返回日志记录器

        Args:
            name: 日志记录器名称
            log_dir: 日志文件目录
            level: 文件日志级别
            console_level: 控制台日志级别

        Returns:
            配置好的日志记录器
        """
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # 避免重复添加处理器
        if logger.handlers:
            return logger

        # 创建日志目录
        os.makedirs(log_dir, exist_ok=True)

        # 文件处理器
        log_file = os.path.join(log_dir, f"{name}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)

        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        cls._loggers[name] = logger
        return logger

    @classmethod
    def get(cls, name: str) -> Optional[logging.Logger]:
        """
        获取已存在的日志记录器

        Args:
            name: 日志记录器名称

        Returns:
            日志记录器，如果不存在则返回 None
        """
        return cls._loggers.get(name)
