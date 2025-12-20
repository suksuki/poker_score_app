#!/bin/bash
# 安装 buildozer 和依赖的脚本
# 使用方法: ./setup_buildozer.sh

set -e

echo "=========================================="
echo "安装 buildozer 和依赖..."
echo "=========================================="
echo ""

# 检查是否在 WSL/Ubuntu 环境中
if [ ! -f /etc/os-release ]; then
    echo "错误: 此脚本需要在 Linux/WSL 环境中运行"
    echo "请在 WSL Ubuntu 终端中运行此脚本"
    exit 1
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    echo "请先安装 Python3: sudo apt-get install python3 python3-pip"
    exit 1
fi

echo "Python 版本:"
python3 --version
echo ""

# 更新系统包
echo "更新系统包..."
sudo apt-get update

# 安装系统依赖
echo "安装系统依赖..."
sudo apt-get install -y \
    git \
    unzip \
    openjdk-17-jdk \
    python3-pip \
    autoconf \
    libtool \
    pkg-config \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libtinfo5 \
    cmake \
    libffi-dev \
    libssl-dev \
    cython

echo ""

# 检查是否使用虚拟环境
if [ -d ".venv" ]; then
    echo "检测到虚拟环境，在虚拟环境中安装..."
    source .venv/bin/activate
    pip install --upgrade pip
    pip install buildozer python-for-android
    echo ""
    echo "✓ 已在虚拟环境中安装 buildozer"
    echo ""
    echo "下次使用时，请先激活虚拟环境："
    echo "  source .venv/bin/activate"
else
    echo "未检测到虚拟环境，询问安装方式..."
    echo ""
    echo "选择安装方式："
    echo "1) 创建虚拟环境并安装（推荐）"
    echo "2) 安装到用户目录 (~/.local/bin)"
    read -p "请选择 (1 或 2): " choice
    
    case $choice in
        1)
            echo "创建虚拟环境..."
            python3 -m venv .venv
            source .venv/bin/activate
            pip install --upgrade pip
            pip install buildozer python-for-android
            echo ""
            echo "✓ 已在虚拟环境中安装 buildozer"
            echo ""
            echo "下次使用时，请先激活虚拟环境："
            echo "  source .venv/bin/activate"
            ;;
        2)
            echo "安装到用户目录..."
            pip3 install --user --upgrade pip
            pip3 install --user buildozer python-for-android
            export PATH=$PATH:~/.local/bin
            echo ""
            echo "✓ 已安装 buildozer 到 ~/.local/bin"
            echo ""
            echo "请确保 ~/.local/bin 在 PATH 中，或运行："
            echo "  export PATH=\$PATH:~/.local/bin"
            ;;
        *)
            echo "无效选择，退出"
            exit 1
            ;;
    esac
fi

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "现在可以运行打包命令："
echo "  buildozer android debug"
echo ""
echo "或使用打包脚本："
echo "  ./build_apk.sh"
echo ""

