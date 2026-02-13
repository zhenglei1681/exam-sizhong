# 授权码使用说明

## 概述

阅卷系统使用授权码进行访问控制。授权码由 `tools/license_generator.py` 生成，并由 `src/auth/license_manager.py` 验证。

## 授权码格式

授权码格式为：`GS1-{Base64数据}-{校验位}`

例如：
```
GS1-eyJleXNl9ZG...xyz-3a1b
```

## 生成授权码

### 方法一：使用命令行工具

```bash
cd tools
python license_generator.py generate --user-id 用户ID --days 365
```

输出示例：
```
==================================================
授权码生成成功
==================================================
授权码: GS1-eyJleXNl9ZG...xyz-3a1b
用户ID: user001
有效天数: 365
有效期至: 2025-02-13
授权类型: standard
==================================================
```

### 方法二：使用 Python 代码

```python
from tools.license_generator import LicenseGenerator

# 创建生成器（使用自定义密钥）
generator = LicenseGenerator(secret_key="your-secret-key")

# 生成授权码
info = generator.generate(user_id="user001", valid_days=365)

print(f"授权码: {info['license_code']}")
```

### 方法三：使用授权服务器

```python
from tools.license_generator import LicenseServer

# 创建服务器
server = LicenseServer(secret_key="your-secret-key")

# 颁发授权码
info = server.issue_license(user_id="user001", valid_days=365)
```

## 验证授权码

### 命令行验证

```bash
cd tools
python license_generator.py verify --license-code GS1-eyJleXNl9ZG...xyz-3a1b
```

### 代码验证

```python
from tools.license_generator import LicenseGenerator

generator = LicenseGenerator(secret_key="your-secret-key")
result = generator.verify("GS1-eyJleXNl9ZG...xyz-3a1b")

if result["valid"]:
    print("授权码有效")
    print(f"有效期至: {result['expiry']}")
else:
    print("授权码无效")
    print(f"原因: {result['reason']}")
```

## 配置授权

### 1. 配置密钥

在 `config/settings.yaml` 中配置授权密钥：

```yaml
license:
  enabled: true
  valid_days: 365
  server_url: ""  # 如需远程验证，填写服务器URL
```

**注意**：`secret_key` 需要在 `src/auth/license_manager.py` 或 `config/settings.yaml` 中配置，确保与生成授权码时使用的密钥一致。

### 2. 在应用中配置密钥

修改 `src/auth/license_manager.py` 的初始化：

```python
# 方式一：硬编码密钥
self.secret_key = "your-secret-key-change-this"

# 方式二：从配置文件读取
self.secret_key = config.get("license", {}).get("secret_key", "default-key")
```

或修改 `config/settings.yaml`：

```yaml
license:
  enabled: true
  secret_key: "your-secret-key-change-this"  # 添加此行
  valid_days: 365
```

### 3. 在 main.py 中传递密钥

```python
# 读取密钥配置
secret_key = config["settings"].get("license", {}).get("secret_key")

# 初始化授权管理器
self.license_manager = LicenseManager(config["settings"], secret_key=secret_key)
```

## 使用授权码

首次运行应用时：

1. 双击运行 `GradingSystem.exe`
2. 系统提示输入授权码
3. 输入生成的授权码
4. 授权成功后，系统会保存授权信息

## 授权信息位置

授权信息保存在：
- **Windows**: `%APPDATA%\grading_system\.grading_system_license`
- **Linux/macOS**: `~/.local/share/grading_system/.grading_system_license`

## 清除授权

如果需要更换授权码：

1. 删除授权文件
2. 重新运行应用并输入新的授权码

或使用代码清除：

```python
license_manager.clear_license()
```

## 安全建议

1. **密钥保护**：将密钥存储在安全的地方，不要硬编码在代码中
2. **远程验证**：生产环境建议使用远程服务器验证
3. **授权期限**：设置合理的有效期，避免长期授权风险
4. **机器绑定**：授权码已绑定机器 ID，无法在其他机器使用

## 远程服务器验证

如需实现远程验证，创建一个简单的 HTTP API：

```python
from flask import Flask, request, jsonify
from tools.license_generator import LicenseGenerator

app = Flask(__name__)
generator = LicenseGenerator(secret_key="your-secret-key")

@app.route('/verify', methods=['POST'])
def verify():
    data = request.json
    license_code = data.get('license_code')
    result = generator.verify(license_code)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000)
```

然后在 `config/settings.yaml` 中配置：

```yaml
license:
  enabled: true
  server_url: "http://your-license-server.com"
```
