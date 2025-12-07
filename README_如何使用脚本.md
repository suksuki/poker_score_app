# 如何使用打包脚本

## 🚀 最简单的方法（推荐）

**直接双击运行 `打包APK.bat` 文件！**

这个批处理文件会自动：
1. 在 WSL 中检查并安装 buildozer（如果需要）
2. 清理之前的构建
3. 开始打包 APK

**无需手动输入任何命令！**

## 📝 其他方法

### 方法 1: 双击运行 .bat 文件

- `打包APK.bat` - 双击即可运行，最简单

### 方法 2: 在 PowerShell 中运行

打开 PowerShell，运行：
```powershell
.\打包APK.ps1
```

### 方法 3: 在 WSL Ubuntu 终端中运行

1. 打开 WSL Ubuntu 终端（按 `Win + R`，输入 `wsl`）
2. 运行：
   ```bash
   cd /home/jin/poker_score_app
   bash 一键安装和打包.sh
   ```

## ⚠️ 重要提示

- **不要**在 PowerShell 中直接运行 `buildozer android` 命令
- **不要**在 PowerShell 中运行 `cd /home/jin/...` 这样的 Linux 路径
- **使用** `.bat` 文件或 `.ps1` 脚本，它们会自动在 WSL 中执行

## 📦 打包完成后

APK 文件会在：
```
\\wsl.localhost\Ubuntu\home\jin\poker_score_app\bin\pokerscore-0.1-arm64-v8a-debug.apk
```

## ⏱️ 首次打包时间

首次打包可能需要 **30-60 分钟**，因为需要下载：
- Android SDK
- Android NDK  
- 编译工具链

请耐心等待，确保网络连接稳定。

