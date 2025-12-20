@echo off
echo 检查 Python 环境...
python --version

echo.
echo 检查 Kivy 是否已安装...
python -c "import kivy" 2>nul
if %errorlevel% equ 0 (
    echo Kivy 已安装
    python -c "import kivy; print('Kivy 版本:', kivy.__version__)"
) else (
    echo Kivy 未安装，正在安装...
    pip install kivy
)

echo.
echo 启动应用...
python main.py
pause

