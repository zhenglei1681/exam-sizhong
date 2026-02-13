"""
授权码生成器

用于生成和验证阅卷系统的授权码
"""
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import secrets


class LicenseGenerator:
    """授权码生成器"""

    def __init__(self, secret_key: str = None):
        """
        初始化授权码生成器

        Args:
            secret_key: 密钥，用于签名和验证
        """
        self.secret_key = secret_key or secrets.token_hex(32)

    def generate(
        self,
        user_id: str,
        valid_days: int = 365,
        license_type: str = "standard"
    ) -> Dict[str, str]:
        """
        生成授权码

        Args:
            user_id: 用户ID
            valid_days: 有效天数
            license_type: 授权类型 (standard, pro, enterprise)

        Returns:
            包含授权信息的字典
        """
        # 时间戳
        timestamp = int(time.time())
        expiry = timestamp + (valid_days * 24 * 60 * 60)

        # 创建授权数据
        license_data = {
            "user_id": user_id,
            "issued_at": timestamp,
            "expiry": expiry,
            "license_type": license_type
        }

        # 生成签名
        signature = self._sign(license_data)

        # 编码为授权码
        license_code = self._encode(license_data, signature)

        return {
            "license_code": license_code,
            "user_id": user_id,
            "valid_days": valid_days,
            "expiry": datetime.fromtimestamp(expiry).strftime("%Y-%m-%d"),
            "license_type": license_type
        }

    def verify(self, license_code: str) -> Dict[str, any]:
        """
        验证授权码

        Args:
            license_code: 授权码

        Returns:
            验证结果字典
        """
        try:
            # 解码授权码
            license_data, signature = self._decode(license_code)

            # 验证签名
            if not self._verify_signature(license_data, signature):
                return {
                    "valid": False,
                    "reason": "签名验证失败"
                }

            # 检查有效期
            if time.time() > license_data["expiry"]:
                return {
                    "valid": False,
                    "reason": "授权已过期"
                }

            return {
                "valid": True,
                "user_id": license_data["user_id"],
                "license_type": license_data["license_type"],
                "expiry": datetime.fromtimestamp(license_data["expiry"]).strftime("%Y-%m-%d"),
                "days_left": (datetime.fromtimestamp(license_data["expiry"]) - datetime.now()).days
            }

        except Exception as e:
            return {
                "valid": False,
                "reason": f"授权码格式错误: {str(e)}"
            }

    def _sign(self, data: Dict) -> str:
        """生成签名"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(f"{data_str}{self.secret_key}".encode()).hexdigest()[:16]

    def _verify_signature(self, data: Dict, signature: str) -> bool:
        """验证签名"""
        return self._sign(data) == signature

    def _encode(self, data: Dict, signature: str) -> str:
        """编码为授权码"""
        data_str = json.dumps(data, sort_keys=True)
        combined = f"{data_str}.{signature}"

        # Base64 编码 + 添加版本和校验位
        import base64
        encoded = base64.b64encode(combined.encode()).decode()

        # 添加版本号和简单校验
        checksum = hashlib.md5(encoded.encode()).hexdigest()[:4]
        return f"GS1-{encoded}-{checksum}"

    def _decode(self, license_code: str) -> tuple:
        """解码授权码"""
        # 移除版本前缀
        if not license_code.startswith("GS1-"):
            raise ValueError("无效的授权码版本")

        # 分离校验位
        parts = license_code[4:].split("-")
        if len(parts) != 2:
            raise ValueError("授权码格式错误")

        encoded, checksum = parts

        # 验证校验位
        if checksum != hashlib.md5(encoded.encode()).hexdigest()[:4]:
            raise ValueError("校验位验证失败")

        # Base64 解码
        import base64
        decoded = base64.b64decode(encoded).decode()

        # 分离数据和签名
        data_str, signature = decoded.rsplit(".", 1)
        data = json.loads(data_str)

        return data, signature


class LicenseServer:
    """模拟授权服务器（用于测试）"""

    def __init__(self, secret_key: str = None):
        self.generator = LicenseGenerator(secret_key)
        self.issued_licenses = []

    def issue_license(
        self,
        user_id: str,
        valid_days: int = 365
    ) -> Dict[str, str]:
        """
        颁发授权码

        Args:
            user_id: 用户ID
            valid_days: 有效天数

        Returns:
            授权信息
        """
        license_info = self.generator.generate(user_id, valid_days)
        self.issued_licenses.append(license_info)
        return license_info

    def verify_license(self, license_code: str) -> Dict[str, any]:
        """
        验证授权码（服务器端验证）

        Args:
            license_code: 授权码

        Returns:
            验证结果
        """
        return self.generator.verify(license_code)

    def list_licenses(self) -> List[Dict]:
        """列出所有已颁发的授权"""
        return self.issued_licenses


def main():
    """命令行工具"""
    import argparse

    parser = argparse.ArgumentParser(description="授权码生成工具")
    parser.add_argument("action", choices=["generate", "verify"],
                      help="操作类型: generate 或 verify")
    parser.add_argument("--user-id", help="用户ID")
    parser.add_argument("--days", type=int, default=365,
                      help="有效天数（默认365）")
    parser.add_argument("--license-code", help="授权码（用于验证）")
    parser.add_argument("--key", help="密钥（默认自动生成）")

    args = parser.parse_args()

    generator = LicenseGenerator(args.key)

    if args.action == "generate":
        if not args.user_id:
            print("错误: 生成授权码需要 --user-id 参数")
            return

        info = generator.generate(args.user_id, args.days)
        print("\n" + "="*50)
        print("授权码生成成功")
        print("="*50)
        print(f"授权码: {info['license_code']}")
        print(f"用户ID: {info['user_id']}")
        print(f"有效天数: {info['valid_days']}")
        print(f"有效期至: {info['expiry']}")
        print(f"授权类型: {info['license_type']}")
        print("="*50)

    elif args.action == "verify":
        if not args.license_code:
            print("错误: 验证授权码需要 --license-code 参数")
            return

        result = generator.verify(args.license_code)
        print("\n" + "="*50)
        if result["valid"]:
            print("授权码验证通过")
            print("="*50)
            print(f"用户ID: {result['user_id']}")
            print(f"授权类型: {result['license_type']}")
            print(f"有效期至: {result['expiry']}")
            print(f"剩余天数: {result['days_left']}")
        else:
            print("授权码验证失败")
            print("="*50)
            print(f"原因: {result['reason']}")
        print("="*50)


if __name__ == "__main__":
    main()
