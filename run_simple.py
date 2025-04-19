"""
禾燃客户管理系统 - 简化版启动器
直接使用简化版应用，避免SQLAlchemy兼容性问题
"""
import sys
import os
import subprocess

def main():
    """
    运行简化版应用，不需要安装其他Python版本
    """
    print("="*65)
    print("禾燃客户管理系统 - 简化版启动器")
    print("该版本使用原生SQLite而不是SQLAlchemy，兼容Python 3.13")
    print("="*65)
    
    # 检查必要的依赖是否安装
    try:
        import flask
        print("✓ Flask已安装")
    except ImportError:
        print("✗ Flask未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "flask==2.3.3", "flask-login==0.6.2", "werkzeug==2.3.7"])
    
    # 检查数据库文件是否存在
    if not os.path.exists('database.db'):
        print("首次运行，正在初始化数据库...")
        from app_simple import init_db
        init_db()
        print("✓ 数据库初始化完成")
    
    # 运行应用
    print("\n正在启动应用...")
    os.environ['FLASK_APP'] = 'app_simple.py'
    subprocess.run([sys.executable, "app_simple.py"])

if __name__ == "__main__":
    main() 