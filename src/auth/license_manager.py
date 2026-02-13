"""
授权码管理模块（完整版）

支持本地验证和远程服务器验证
"""
import os
import hashlib
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any


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


class LicenseManager:
    """授权管理器"""

    def __init__(self, config: dict, secret_key: str = None):
        """
        初始化授权管理器

        Args:
            config: 配置字典
            secret_key: 密钥（用于验证授权码）
        """
        self.enabled = config.get("license", {}).get("enabled", False)
        self.valid_days = config.get("license", {}).get("valid_days", 365)

        # 授权文件路径
        app_data_dir = self._get_app_data_dir()
        self.license_file = os.path.join(app_data_dir, ".grading_system_license")

        # 远程验证配置
        self.server_url = config.get("license", {}).get("server_url", "")

        # 密钥（与 license_generator.py 使用相同的密钥）
        self.secret_key = secret_key or "default-secret-key-change-this"

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

        # 基本格式验证
        if not license_code or len(license_code) < 16:
            return False

        # 方式一：远程服务器验证
        if self.server_url:
            return self._verify_remote(license_code)

        # 方式二：本地验证（使用 tools/license_generator.py 的格式）
        return self._verify_local(license_code)

    def _verify_local(self, license_code: str) -> bool:
        """本地验证授权码"""
        try:
            # 使用与 license_generator.py 相同的密钥进行验证
            import base64

            # 解码授权码
            if not license_code.startswith("GS1-"):
                return False

            parts = license_code[4:].split("-")
            if len(parts) != 2:
                return False

            encoded, checksum = parts

            # 验证校验位
            if checksum != hashlib.md5(encoded.encode()).hexdigest()[:4]:
                return False

            # Base64 解码
            decoded = base64.b64decode(encoded).decode()

            # 分离数据和签名
            data_str, signature = decoded.rsplit(".", 1)
            data = json.loads(data_str)

            # 验证签名
            data_str_sorted = json.dumps(data, sort_keys=True)
            expected_signature = hashlib.sha256(
                f"{data_str_sorted}{self.secret_key}".encode()
            ).hexdigest()[:16]

            if signature != expected_signature:
                return False

            # 检查有效期
            if time.time() > data.get("expiry", 0):
                return False

            return True

        except Exception:
            return False

    def _verify_remote(self, license_code: str) -> bool:
        """远程服务器验证"""
        try:
            import requests

            response = requests.post(
                self.server_url + "/verify",
                json={"license_code": license_code},
                timeout=10
            )
            data = response.json()
            return data.get("valid", False)
        except:
            # 服务器不可用时回退到本地验证
            return self._verify_local(license_code)

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
            valid_days = license_data.get("valid_days", self.valid_days)
            valid_until = timestamp + (valid_days * 24 * 60 * 60)

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

        # 解析授权码获取详细信息
        try:
            import base64

            if not license_code.startswith("GS1-"):
                raise ValueError("无效的授权码格式")

            parts = license_code[4:].split("-")
            encoded = parts[0]
            decoded = base64.b64decode(encoded).decode()
            data_str, signature = decoded.rsplit(".", 1)
            data = json.loads(data_str)

            # 计算过期时间戳
            expiry = data.get("expiry", int(time.time()))

            license_data = {
                "license_code": license_code,
                "user_id": data.get("user_id", ""),
                "license_type": data.get("license_type", ""),
                "timestamp": int(time.time()),
                "machine_id": get_machine_id(),
                "valid_days": self.valid_days
            }

            self._save_license_data(license_data)
            return True

        except Exception:
            # 解析失败，使用原始保存方式
            license_data = {
                "license_code": license_code,
                "timestamp": int(time.time()),
                "machine_id": get_machine_id(),
                "valid_days": self.valid_days
            }
            self._save_license_data(license_data)
            return True

    def get_license_info(self) -> Dict[str, Any]:
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
            valid_days = license_data.get("valid_days", self.valid_days)
            valid_until = datetime.fromtimestamp(
                timestamp + (valid_days * 24 * 60 * 60)
            )
            days_left = (valid_until - datetime.now()).days

            return {
                "authorized": True,
                "user_id": license_data.get("user_id", ""),
                "license_type": license_data.get("license_type", ""),
                "valid_until": valid_until.strftime("%Y-%m-%d"),
                "days_left": max(0, days_left)
            }
        except Exception:
            return {"authorized": False}

    def _load_license_data(self) -> Dict[str, Any]:
        """加载授权数据"""
        with open(self.license_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_license_data(self, data: Dict[str, Any]) -> None:
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
