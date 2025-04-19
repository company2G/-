"""
禾燃客户管理系统 - 启动脚本
该脚本启动完整功能的客户管理系统(SQLite版)
"""
import os
import sys
import subprocess
import webbrowser
from time import sleep
import sqlite3
import argparse  # 添加命令行参数解析
import functools
from flask import g, redirect, url_for, flash

def get_script_dir():
    """获取当前脚本所在目录"""
    return os.path.dirname(os.path.abspath(__file__))

def init_db_manually():
    """手动初始化数据库"""
    print("正在手动初始化数据库...")
    
    # 获取当前脚本所在目录
    script_dir = get_script_dir()
    
    # 数据库文件路径
    db_path = os.path.join(script_dir, 'database.db')
    schema_path = os.path.join(script_dir, 'schema.sql')
    
    # 检查schema.sql是否存在
    if not os.path.exists(schema_path):
        print(f"错误：无法找到schema.sql文件。请确保该文件存在于目录: {script_dir}")
        return False
    
    # 确保数据库文件不存在时创建新数据库
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"已删除旧数据库文件: {db_path}")
        except PermissionError:
            print("警告：数据库文件正在被其他程序使用，无法删除。")
            print("请关闭所有可能使用该数据库的程序，然后重试。")
            return False
        except Exception as e:
            print(f"删除旧数据库时出错: {e}")
            return False
    
    try:
        # 创建新连接
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 读取和执行schema.sql
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
            c.executescript(schema_sql)
        
        # 提交更改并关闭连接
        conn.commit()
        conn.close()
        print(f"✓ 数据库已成功初始化: {db_path}")
        return True
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
        return False

def main():
    """主启动函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='禾燃客户管理系统启动器')
    parser.add_argument('--reset-db', action='store_true', help='强制重置数据库')
    args = parser.parse_args()
    
    print("="*65)
    print("禾燃客户管理系统 - 启动器")
    print("="*65)
    
    # 获取当前脚本所在目录
    script_dir = get_script_dir()
    os.chdir(script_dir)  # 将工作目录设置为脚本所在目录
    
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查必要的依赖是否安装
    try:
        import flask
        import flask_login
        print("✓ 依赖已安装")
    except ImportError:
        print("正在安装必要的依赖...")
        subprocess.run([sys.executable, "-m", "pip", "install", "flask==2.3.3", "flask-login==0.6.2", "werkzeug==2.3.7"])
        print("✓ 依赖安装完成")
    
    # 检查数据库是否需要初始化
    db_path = os.path.join(script_dir, 'database.db')
    db_needs_init = not os.path.exists(db_path) or args.reset_db
    
    # 手动初始化数据库
    if db_needs_init:
        if args.reset_db:
            print("收到重置数据库的指令，将重新初始化数据库...")
        else:
            print("首次运行，需要初始化数据库...")
            
        if not init_db_manually():
            print("数据库初始化失败，程序退出。")
            return
    
    # 运行应用
    print("\n正在启动禾燃客户管理系统...")
    
    # 启动Flask应用
    flask_process = subprocess.Popen([sys.executable, os.path.join(script_dir, "start_app.py")])
    
    # 等待服务器启动
    print("等待服务器启动...")
    sleep(2)
    
    # 自动打开浏览器
    print("正在打开浏览器...")
    webbrowser.open("http://127.0.0.1:5000")
    
    print("\n系统已启动！按Ctrl+C结束程序。")
    
    try:
        # 保持程序运行
        flask_process.wait()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        flask_process.terminate()
        print("服务器已关闭。")

if __name__ == "__main__":
    main() 