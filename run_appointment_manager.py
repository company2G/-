#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
禾燃客户管理系统 - 预约管理独立模块启动器
使用单独的端口运行预约管理模块，方便集中管理预约
"""

import os
import sys
import time
import socket
import subprocess
import webbrowser
import argparse

def get_ip_address():
    """获取本机IP地址"""
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

def main():
    """主函数"""
    print("=" * 65)
    print("禾燃客户管理系统 - 预约管理模块独立启动器")
    print("=" * 65)
    
    parser = argparse.ArgumentParser(description='启动禾燃客户管理系统预约管理模块')
    parser.add_argument('--port', type=int, default=5050, help='指定端口号(默认: 5050)')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='指定主机地址(默认: 0.0.0.0,允许所有网络接口)')
    parser.add_argument('--no-browser', action='store_true', help='不自动打开浏览器')
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
    
    # 检查文件是否存在
    app_path = os.path.join(script_dir, 'app.py')
    if not os.path.exists(app_path):
        print(f"错误: 未找到应用文件 {app_path}")
        return
    
    # 启动应用
    print("\n正在启动预约管理模块...")
    
    # 获取本机IP地址
    local_ip = get_ip_address()
    port = args.port
    host = args.host
    
    # 设置环境变量
    my_env = os.environ.copy()
    my_env["FLASK_APP"] = "app.py"
    my_env["FLASK_ENV"] = "development"
    
    # 命令行参数
    cmd = [
        python_executable, 
        "app.py"
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
        
        print("\n您可以通过以下地址访问预约管理系统:")
        print(f"- 本地访问: {local_url}")
        print(f"- 局域网访问: {network_url}")
        
        # 自动打开浏览器
        if not args.no_browser:
            print("正在打开浏览器...")
            webbrowser.open(local_url)
    else:
        print("\n✗ 服务器启动失败")
        proc.terminate()
        return
    
    print("\n预约管理模块已启动！按Ctrl+C结束程序。")
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n正在关闭服务器...")
        proc.terminate()
        proc.wait()
        print("服务器已关闭")

if __name__ == "__main__":
    main() 