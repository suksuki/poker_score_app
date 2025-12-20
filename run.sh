#!/bin/bash

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 定义虚拟环境路径
VENV_PYTHON="$DIR/.venv/bin/python3"

# 检查虚拟环境是否存在
if [ ! -f "$VENV_PYTHON" ]; then
    echo "错误：未找到虚拟环境，请确保 .venv 目录存在。"
    echo "您可能需要运行 setup_buildozer.sh 或手动创建虚拟环境。"
    exit 1
fi

echo "使用虚拟环境启动应用..."
"$VENV_PYTHON" "$DIR/main.py"
