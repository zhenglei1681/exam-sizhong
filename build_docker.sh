#!/bin/bash
# 交互式 Docker 打包脚本（更安全的 Token 处理）

echo "=========================================="
echo "阅卷系统 - Docker 打包工具"
echo "=========================================="

# 构建镜像
echo "1. 构建 Docker 镜像..."
docker build -t grading-system-builder .

# 创建输出目录
mkdir -p dist

# 运行容器并提取打包结果
echo "2. 提取可执行文件..."
docker run --rm -v "$(pwd)/dist:/output" grading-system-builder

echo ""
echo "=========================================="
echo "打包完成！"
echo "可执行文件位置: dist/GradingSystem"
echo "=========================================="

# 获取文件信息
if [ -f "dist/GradingSystem" ]; then
    echo ""
    echo "文件信息:"
    ls -lh dist/GradingSystem
    echo ""
    echo "分发说明:"
    echo "1. 将 dist/GradingSystem 复制到目标系统"
    echo "2. 复制 config/ 目录到相同位置"
    echo "3. 运行: ./GradingSystem"
    echo ""
    echo "注意: 目标系统需要安装以下系统依赖:"
    echo "  - libgl1-mesa-glx"
    echo "  - libglib2.0-0"
    echo ""
    echo "在 Ubuntu/Debian 上安装:"
    echo "  sudo apt-get install libgl1-mesa-glx libglib2.0-0"
fi
