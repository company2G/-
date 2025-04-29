#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
禾燃客户管理系统 - 支持外网访问的启动器
"""

import os
import sys
import time
import socket
import subprocess
import webbrowser
import argparse
import sqlite3
import shutil

def get_ip_address():
    """获取本22222222222222222222222222222机IP地址"""
    try:
        # 创建一个临时套接字连接到一个公共服务器，获取本地IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # 如果上述方法失败，尝试另一种方法
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return ip

def wait_for_server(host, port, timeout=10):
    """等待服务器启动"""
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            print(f"等待服务器启动超时 ({timeout}秒)")
            return False
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return True
        except Exception:
            pass
        
        time.sleep(0.5)
        print(".", end="", flush=True)

def init_db_manually():
    """手动初始化数据库"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(script_dir, 'schema.sql')
        db_path = os.path.join(script_dir, 'database.db')
        
        if not os.path.exists(schema_path):
            print(f"错误: 未找到数据库模式文件 {schema_path}")
            return False
        
        # 如果存在旧数据库则删除
        if os.path.exists(db_path):
            backup_path = db_path + '.backup_' + str(int(time.time()))
            shutil.copy2(db_path, backup_path)
            print(f"已将旧数据库备份到: {backup_path}")
            os.remove(db_path)
            print("已删除旧数据库")
        
        # 创建新数据库
        conn = sqlite3.connect(db_path)
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        
        print(f"成功创建新数据库: {db_path}")
        return True
    except Exception as e:
        print(f"初始化数据库失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 65)
    print("禾燃客户管理系统 - 网络版启动器")
    print("=" * 65)
    
    parser = argparse.ArgumentParser(description='启动禾燃客户管理系统(支持外网访问)')
    parser.add_argument('--port', type=int, default=5000, help='指定端口号(默认: 5000)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='指定主机地址(默认: 0.0.0.0,允许所有网络接口)')
    parser.add_argument('--no-browser', action='store_true', help='不自动打开浏览器')
    parser.add_argument('--reset-db', action='store_true', help='重置数据库')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()
    
    # 获取工作目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"当前工作目录: {script_dir}")
    os.chdir(script_dir)
    
    # 检查Python环境
    venv_path = os.path.join(script_dir, ".venv")
    if os.path.exists(venv_path):
        # 使用虚拟环境中的Python
        if sys.platform == 'win32':
            python_executable = os.path.join(venv_path, "Scripts", "python.exe")
        else:
            python_executable = os.path.join(venv_path, "bin", "python")
    else:
        # 使用系统Python
        python_executable = sys.executable
    
    # 检查依赖
    try:
        import flask
        print("✓ 依赖已安装")
    except ImportError:
        print("安装依赖...")
        subprocess.check_call([python_executable, "-m", "pip", "install", "flask", "flask-login"])
        print("✓ 依赖安装完成")
    
    # 检查是否需要重置数据库
    if args.reset_db:
        print("\n正在重置数据库...")
        if init_db_manually():
            print("✓ 数据库重置成功")
        else:
            print("✗ 数据库重置失败")
            return
    else:
        # 检查数据库是否存在
        db_path = os.path.join(script_dir, 'database.db')
        if not os.path.exists(db_path):
            print("\n未找到数据库，正在初始化...")
            if init_db_manually():
                print("✓ 数据库初始化成功")
            else:
                print("✗ 数据库初始化失败")
                return
    
    # 启动应用
    print("\n正在启动禾燃客户管理系统...")
    
    # 获取本机IP地址
    local_ip = get_ip_address()
    port = args.port
    host = args.host
    
    # 设置环境变量
    my_env = os.environ.copy()
    my_env["FLASK_APP"] = "app_simple.py"
    if args.debug:
        my_env["FLASK_ENV"] = "development"
        my_env["FLASK_DEBUG"] = "1"
    else:
        my_env["FLASK_ENV"] = "production"
    
    # 命令行参数
    cmd = [
        python_executable, 
        "-m", "flask", "run", 
        "--host", host, 
        "--port", str(port),
        "--no-reload"  # 禁用自动重载，提高稳定性
    ]
    
    # 启动进程
    proc = subprocess.Popen(cmd, env=my_env)
    
    # 等待服务器启动
    print("等待服务器启动...", end="", flush=True)
    if wait_for_server('localhost', port):
        print("\n✓ 服务器已启动")
        
        # 打印访问地址
        local_url = f"http://127.0.0.1:{port}"
        network_url = f"http://{local_ip}:{port}"
        
        print("\n您可以通过以下地址访问系统:")
        print(f"- 本地访问: {local_url}")
        print(f"- 局域网访问: {network_url}")
        print("\n提示: 局域网内的其他设备需要使用局域网地址访问")
        
        # 自动打开浏览器
        if not args.no_browser:
            print("正在打开浏览器...")
            webbrowser.open(local_url)
    else:
        print("\n✗ 服务器启动失败")
        proc.terminate()
        return
    
    print("\n系统已启动！按Ctrl+C结束程序。")
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        proc.terminate()
        proc.wait()
        print("服务器已关闭")

if __name__ == "__main__":
    main() 