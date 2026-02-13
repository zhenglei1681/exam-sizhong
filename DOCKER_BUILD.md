# Docker 打包说明

## 快速开始

```bash
./build_docker.sh
```

## 详细步骤

### 1. 构建镜像

```bash
docker build -t grading-system-builder .
```

### 2. 提取可执行文件

```bash
docker run --rm -v "$(pwd)/dist:/output" grading-system-builder
```

### 3. 分发

打包完成后，可执行文件位于 `dist/GradingSystem`

分发时需要：
1. 复制 `dist/GradingSystem` 到目标系统
2. 复制 `config/` 目录到相同位置
3. 运行 `./GradingSystem`

## 目标系统依赖

在 Ubuntu/Debian 上运行可执行文件前，需要安装：

```bash
sudo apt-get install libgl1-mesa-glx libglib2.0-0
```

## Windows 打包

如需 Windows exe 文件，请在 Windows 环境下执行：

```bash
pip install -r requirements.txt
playwright install chromium
cd build
python build_exe.py
```

生成的 exe 文件在 `dist/GradingSystem.exe`
