"""
禾燃客户管理系统启动脚本
这个脚本用于避免模块导入的循环依赖问题
"""
import sys
import subprocess

def main():
    """
    尝试使用Python 3.10/3.11运行应用
    如果不可用，提示用户安装合适的Python版本
    """
    # 尝试使用python3.10运行
    try:
        subprocess.run(["python3.10", "app.py"])
        return
    except FileNotFoundError:
        pass
    
    # 尝试使用python3.11运行
    try:
        subprocess.run(["python3.11", "app.py"])
        return
    except FileNotFoundError:
        pass
    
    # 如果上述都失败，给出提示
    print("=================================================================")
    print("错误: 当前Python版本(3.13)与SQLAlchemy不兼容")
    print("请安装Python 3.10或3.11版本并创建新的虚拟环境:")
    print("\n1. 安装Python 3.10/3.11")
    print("2. 创建新的虚拟环境: python3.10 -m venv .venv_py310")
    print("3. 激活环境: .venv_py310\\Scripts\\activate (Windows)")
    print("   或 source .venv_py310/bin/activate (Linux/Mac)")
    print("4. 安装依赖: pip install -r requirements.txt")
    print("5. 运行应用: python app.py")
    print("=================================================================")

if __name__ == "__main__":
    main() 