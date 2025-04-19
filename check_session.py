#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查用户会话信息的脚本
用于调试用户角色权限问题
"""

import os
import sys
import sqlite3
from datetime import datetime
import flask
import json

# 获取数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def connect_db():
    """连接到数据库"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_details(username):
    """获取用户详细信息"""
    try:
        conn = connect_db()
        cur = conn.cursor()
        
        # 获取用户信息
        user = cur.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        
        if not user:
            print(f"错误: 用户 '{username}' 不存在")
            return None
        
        # 将SQLite Row对象转换为字典
        user_dict = {key: user[key] for key in user.keys()}
        
        # 打印详细信息
        print("\n用户详细信息:")
        print("-" * 50)
        for key, value in user_dict.items():
            print(f"{key}: {value}")
        print("-" * 50)
        
        return user_dict
        
    except Exception as e:
        print(f"错误: {str(e)}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def check_auth_decorator():
    """检查auth装饰器的实现"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(script_dir, 'app_simple.py')
        
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找admin_required实现
        import re
        admin_decorator = re.search(r'def admin_required\(view\):(.*?)return wrapped_view', content, re.DOTALL)
        
        if admin_decorator:
            print("\nadmin_required装饰器实现:")
            print("-" * 50)
            print(admin_decorator.group(0))
            print("-" * 50)
        else:
            print("未找到admin_required装饰器实现")
            
        # 查找User类的is_admin实现
        user_class = re.search(r'class User\(UserMixin\):(.*?)# 用户加载函数', content, re.DOTALL)
        if user_class:
            print("\nUser类实现:")
            print("-" * 50)
            print(user_class.group(0))
            print("-" * 50)
        
    except Exception as e:
        print(f"分析代码出错: {str(e)}")

def fix_user_admin_flag(username):
    """修复用户的is_admin标志"""
    try:
        conn = connect_db()
        cur = conn.cursor()
        
        # 获取用户信息
        user = cur.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        
        if not user:
            print(f"错误: 用户 '{username}' 不存在")
            return False
        
        # 确保role是admin
        if user['role'] != 'admin':
            print(f"更新 '{username}' 的角色为admin...")
            cur.execute('UPDATE user SET role = ? WHERE username = ?', ('admin', username))
            conn.commit()
            print(f"成功更新 '{username}' 角色为admin")
        
        # 确保client_id为NULL（如果有这个字段）
        if 'client_id' in user.keys() and user['client_id'] is not None:
            print(f"重置 '{username}' 的client_id为NULL...")
            cur.execute('UPDATE user SET client_id = NULL WHERE username = ?', (username,))
            conn.commit()
            print(f"成功重置 '{username}' 的client_id")
        
        return True
    except Exception as e:
        print(f"错误: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("禾燃客户管理系统 - 会话调试工具")
    print("=" * 50)
    
    username = "kevin"  # 默认检查kevin用户
    if len(sys.argv) > 1:
        username = sys.argv[1]
    
    # 获取用户详情
    user_info = get_user_details(username)
    
    # 分析代码
    check_auth_decorator()
    
    # 修复用户标志
    if user_info and user_info.get('role') == 'admin':
        print(f"\n正在修复 '{username}' 的管理员标志...")
        if fix_user_admin_flag(username):
            print("\n操作完成。请尝试以下步骤：")
            print("1. 完全退出系统")
            print("2. 清除浏览器缓存和Cookie")
            print("3. 重新登录系统")
            print("\n如果仍然有问题，可能需要检查服务器日志或应用程序代码。")
    else:
        print(f"\n用户 '{username}' 不是管理员，请先设置其角色为admin。") 