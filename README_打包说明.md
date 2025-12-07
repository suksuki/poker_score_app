# 打包 APK 说明

## ⚠️ 重要提示

**buildozer 必须在 WSL Ubuntu 环境中运行，不能在 Windows PowerShell 中直接运行！**

## 🚀 快速开始

### 方法 1: 使用 Windows 批处理文件（最简单）

1. **首次使用 - 安装 buildozer**
   - 双击运行 `在WSL中安装buildozer.bat`
   - 等待安装完成

2. **打包 APK**
   - 双击运行 `在WSL中打包.bat`
   - 等待打包完成（首次可能需要很长时间）

### 方法 2: 在 WSL Ubuntu 终端中运行（推荐）

1. **打开 WSL Ubuntu 终端**
   - 按 `Win + R`，输入 `wsl` 或 `ubuntu` 回车
   - 或在开始菜单搜索 "Ubuntu"

2. **进入项目目录**
   ```bash
   cd /home/jin/poker_score_app
   ```

3. **安装 buildozer（首次需要）**
   ```bash
   chmod +x setup_buildozer.sh
   ./setup_buildozer.sh
   ```

4. **打包 APK**
   ```bash
   chmod +x build_apk.sh
   ./build_apk.sh
   ```

   或直接使用 buildozer：
   ```bash
   buildozer android clean
   buildozer android debug
   ```

## 📁 文件说明

- `在WSL中安装buildozer.bat` - Windows 批处理文件，在 WSL 中安装 buildozer
- `在WSL中打包.bat` - Windows 批处理文件，在 WSL 中打包 APK
- `setup_buildozer.sh` - WSL 中的安装脚本
- `build_apk.sh` - WSL 中的打包脚本
- `安装和打包说明.md` - 详细说明文档

## ⏱️ 首次打包时间

首次打包可能需要 **30-60 分钟**，因为需要下载：
- Android SDK
- Android NDK
- 编译工具链
- Python 依赖

请确保：
- 网络连接稳定
- 有足够的磁盘空间（至少 5GB）
- 有足够的耐心等待

## 📦 打包结果

打包完成后，APK 文件位于：
```
\\wsl.localhost\Ubuntu\home\jin\poker_score_app\bin\pokerscore-0.1-arm64-v8a-debug.apk
```

## ❓ 常见问题

### Q: 为什么不能在 PowerShell 中直接运行？

A: buildozer 是 Linux 工具，需要 Linux 环境。Windows 需要通过 WSL 来运行。

### Q: 打包失败怎么办？

A: 
1. 检查是否在 WSL 环境中运行
2. 检查是否安装了所有依赖
3. 查看错误信息，根据提示解决问题
4. 可以尝试清理后重新打包：`buildozer android clean`

### Q: 图标还是不显示？

A: 
1. 确认已使用最新的代码（已修复图标问题）
2. 重新打包：`buildozer android clean && buildozer android debug`
3. 检查 `assets/icons/` 目录中的图标文件是否存在

### Q: 如何加快打包速度？

A:
- 使用 SSD 硬盘
- 确保有足够的内存（建议 8GB+）
- 关闭其他占用资源的程序
- 使用虚拟环境可以避免重复安装依赖

## 🔧 手动安装步骤（如果脚本失败）

在 WSL Ubuntu 终端中：

```bash
cd /home/jin/poker_score_app

# 安装系统依赖
sudo apt-get update
sudo apt-get install -y git unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev cython

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装 buildozer
pip install --upgrade pip
pip install buildozer python-for-android

# 打包
buildozer android debug
```

