#!/bin/bash
# 检查并安装 Kivy，然后运行应用

echo "检查 Python 环境..."
python3 --version

echo ""
echo "检查 Kivy 是否已安装..."
if python3 -c "import kivy" 2>/dev/null; then
    echo "Kivy 已安装"
    python3 -c "import kivy; print('Kivy 版本:', kivy.__version__)"
else
    echo "Kivy 未安装，正在安装..."
    pip3 install kivy
fi

echo ""
echo "启动应用..."
python3 main.py

