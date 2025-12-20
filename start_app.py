#!/usr/bin/env python3
"""
快速启动脚本 - 检查依赖并运行应用
"""
import sys
import subprocess

def check_and_install_kivy():
    """检查 Kivy 是否已安装，如果没有则安装"""
    try:
        import kivy
        print(f"✓ Kivy 已安装，版本: {kivy.__version__}")
        return True
    except ImportError:
        print("✗ Kivy 未安装，正在安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "kivy"])
            print("✓ Kivy 安装完成")
            return True
        except Exception as e:
            print(f"✗ 安装 Kivy 失败: {e}")
            print("\n请手动运行: pip install kivy")
            return False

def main():
    print("=" * 50)
    print("Poker Score App - 启动中...")
    print("=" * 50)
    print()
    
    # 检查 Python 版本
    print(f"Python 版本: {sys.version}")
    print()
    
    # 检查并安装 Kivy
    if not check_and_install_kivy():
        print("\n无法启动应用，请先安装 Kivy")
        input("\n按 Enter 键退出...")
        return
    
    print()
    print("=" * 50)
    print("正在启动应用...")
    print("=" * 50)
    print()
    
    # 运行主应用
    try:
        import main
        from main import PokerScoreApp
        app = PokerScoreApp()
        app.run()
    except Exception as e:
        print(f"\n✗ 启动应用时出错: {e}")
        import traceback
        traceback.print_exc()
        input("\n按 Enter 键退出...")

if __name__ == "__main__":
    main()

