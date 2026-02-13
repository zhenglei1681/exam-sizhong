# Docker 镜像用于打包阅卷系统
FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libgl1-mesa-glx \
    libglib2.0-0 \
    nvidia-cuda-toolkit \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器
RUN playwright install chromium

# 安装 PyInstaller
RUN pip install pyinstaller

# 复制项目文件
COPY . .

# 打包为单文件可执行
RUN pyinstaller --name=GradingSystem \
    --onefile \
    --add-data=config:config \
    --add-data=src:src \
    --hidden-import=playwright.async_api \
    --hidden-import=paddleocr \
    --hidden-import=paddlepaddle \
    --clean \
    --noconfirm \
    main.py

# 复制打包结果到输出目录
RUN mkdir -p /output && cp dist/GradingSystem /output/

# 输出目录
VOLUME ["/output"]

# 默认命令
CMD ["bash"]
