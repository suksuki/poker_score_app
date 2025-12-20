#!/bin/bash
# 打包 APK 脚本
# 使用方法: ./build_apk.sh

set -e

echo "=========================================="
echo "开始打包 APK..."
echo "=========================================="
echo ""

# 检查 buildozer 是否安装
if ! command -v buildozer &> /dev/null; then
    echo "错误: buildozer 未安装"
    echo "请运行: pip install buildozer"
    exit 1
fi

# 检查图标文件是否存在
echo "检查资源文件..."
if [ ! -f "assets/icons/trophy_gold.png" ]; then
    echo "警告: assets/icons/trophy_gold.png 不存在"
fi
if [ ! -f "assets/icons/trophy_gray.png" ]; then
    echo "警告: assets/icons/trophy_gray.png 不存在"
fi
if [ ! -f "assets/fonts/NotoSansSC-Regular.ttf" ]; then
    echo "警告: assets/fonts/NotoSansSC-Regular.ttf 不存在"
fi

echo ""
echo "清理之前的构建..."
buildozer android clean 2>/dev/null || true

echo ""
echo "开始构建 APK (debug 版本)..."
echo "这可能需要一些时间，请耐心等待..."
echo ""

# 构建 debug APK
buildozer android debug

echo ""
echo "=========================================="
echo "构建完成！"
echo "=========================================="
echo ""
echo "APK 文件位置: bin/pokerscore-*.apk"
echo ""
ls -lh bin/*.apk 2>/dev/null || echo "未找到 APK 文件"

