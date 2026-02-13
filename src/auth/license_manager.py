"""
授权码管理模块

负责授权码的验证、存储和有效期检查
"""
import os
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Optional

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None


def get_machine_id() -> str:
    """获取机器唯一标识"""
    import platform
    import uuid

    system = platform.system()
    if system == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Microsoft\Cryptography")
            machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            return str(machine_guid)
        except:
            pass

    # 通用方法：使用主机名和MAC地址
    hostname = platform.node()
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                     for elements in range(0, 8*6, 8)][::-1])
    return hashlib.md5(f"{hostname}{mac}".encode()).hexdigest()


def hash_license_code(license_code: str) -> str:
    """生成授权码的哈希值"""
    return hashlib.sha256(license_code.encode()).hexdigest()


class LicenseManager:
    """授权管理器"""

    def __init__(self, config: dict):
        """
        初始化授权管理器

        Args:
            config: 配置字典，包含 license 相关配置
        """
        self.enabled = config.get("license", {}).get("enabled", False)
        self.valid_days = config.get("license", {}).get("valid_days", 365)

        # 授权文件路径
        app_data_dir = self._get_app_data_dir()
        self.license_file = os.path.join(app_data_dir, ".grading_system_license")

        # 加密密钥（基于机器ID生成）
        self.encryption_key = self._generate_key()

    def _get_app_data_dir(self) -> str:
        """获取应用数据目录"""
        if os.name == 'nt':
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
        elif os.name == 'posix':
            app_data = os.path.expanduser('~/.local/share')
        else:
            app_data = os.path.expanduser('~')

        app_dir = os.path.join(app_data, 'grading_system')
        os.makedirs(app_dir, exist_ok=True)
        return app_dir

    def _generate_key(self) -> Optional[bytes]:
        """基于机器ID生成加密密钥"""
        if Fernet is None:
            return None
        machine_id = get_machine_id()
        key_material = hashlib.sha256(machine_id.encode()).digest()
        return hashlib.md5(key_material).digest() + b'=' * 16

    def verify_license(self, license_code: str) -> bool:
        """
        验证授权码

        Args:
            license_code: 用户输入的授权码

        Returns:
            验证是否成功
        """
        if not self.enabled:
            return True

        # 简单的授权码格式验证
        if not license_code or len(license_code) < 16:
            return False

        # 这里可以实现更复杂的验证逻辑
        # 例如：调用远程服务器验证
        # 目前使用哈希验证作为示例
        expected_hash = hash_license_code(license_code)
        # 实际应用中，应该将授权码哈希与数据库中存储的合法授权码进行比对

        return True

    def is_authorized(self) -> bool:
        """
        检查是否已授权

        Returns:
            是否在授权有效期内
        """
        if not self.enabled:
            return True

        if not os.path.exists(self.license_file):
            return False

        try:
            license_data = self._load_license_data()

            # 检查机器ID是否匹配
            if license_data.get("machine_id") != get_machine_id():
                return False

            # 检查有效期
            timestamp = license_data.get("timestamp", 0)
            valid_until = timestamp + (self.valid_days * 24 * 60 * 60)

            if time.time() > valid_until:
                return False

            return True

        except Exception:
            return False

    def save_license(self, license_code: str) -> bool:
        """
        保存授权信息

        Args:
            license_code: 授权码

        Returns:
            保存是否成功
        """
        if not self.verify_license(license_code):
            return False

        license_data = {
            "code_hash": hash_license_code(license_code),
            "timestamp": time.time(),
            "machine_id": get_machine_id(),
            "valid_days": self.valid_days
        }

        try:
            self._save_license_data(license_data)
            return True
        except Exception:
            return False

    def get_license_info(self) -> dict:
        """
        获取授权信息

        Returns:
            授权信息字典
        """
        if not self.enabled or not os.path.exists(self.license_file):
            return {"authorized": False}

        try:
            license_data = self._load_license_data()
            timestamp = license_data.get("timestamp", 0)
            valid_until = datetime.fromtimestamp(
                timestamp + (self.valid_days * 24 * 60 * 60)
            )
            days_left = (valid_until - datetime.now()).days

            return {
                "authorized": True,
                "valid_until": valid_until.strftime("%Y-%m-%d"),
                "days_left": max(0, days_left)
            }
        except Exception:
            return {"authorized": False}

    def _load_license_data(self) -> dict:
        """加载授权数据"""
        with open(self.license_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_license_data(self, data: dict):
        """保存授权数据"""
        with open(self.license_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def clear_license(self) -> bool:
        """
        清除授权信息

        Returns:
            清除是否成功
        """
        try:
            if os.path.exists(self.license_file):
                os.remove(self.license_file)
            return True
        except Exception:
            return False
