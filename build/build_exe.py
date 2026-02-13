"""
PyInstaller 打包脚本

将阅卷系统打包为 Windows exe 可执行文件
"""
import os
import subprocess
import sys


def build_exe():
    """执行打包"""
    print("=" * 60)
    print("阅卷系统 - 打包工具")
    print("=" * 60)

    # 检查 PyInstaller 是否安装
    try:
        import PyInstaller
    except ImportError:
        print("错误: PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        sys.exit(1)

    # 项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))

    # PyInstaller 命令参数
    cmd = [
        "pyinstaller",
        "--name=GradingSystem",
        "--onefile",
        "--windowed",
        "--add-data=config;config",
        "--add-data=src;src",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=playwright.async_api",
        "--hidden-import=paddleocr",
        "--hidden-import=paddlepaddle",
        "--clean",
        "--noconfirm",
        "main.py"
    ]

    print(f"\n工作目录: {project_root}")
    print("\n开始打包...")
    print("-" * 60)

    try:
        # 执行打包
        result = subprocess.run(cmd, cwd=project_root, check=True)

        print("-" * 60)
        print("\n打包成功！")
        print(f"\n可执行文件位置: {os.path.join(project_root, 'dist', 'GradingSystem.exe')}")

    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build_exe()
