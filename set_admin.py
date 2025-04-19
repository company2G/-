#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
设置用户为管理员权限的脚本
使用方法: python set_admin.py <用户名>
"""

import os
import sys
import sqlite3
from datetime import datetime

# 获取数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def connect_db():
    """连接到数据库"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def set_user_as_admin(username):
    """将指定用户设置为管理员"""
    try:
        # 连接数据库
        conn = connect_db()
        cur = conn.cursor()
        
        # 检查用户是否存在
        user = cur.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        
        if not user:
            print(f"错误: 用户 '{username}' 不存在")
            return False
        
        # 检查用户当前角色
        if user['role'] == 'admin':
            print(f"用户 '{username}' 已经是管理员")
            return True
        
        # 更新用户角色为管理员
        cur.execute('UPDATE user SET role = ? WHERE username = ?', ('admin', username))
        conn.commit()
        
        print(f"成功: 用户 '{username}' 已设置为管理员")
        return True
        
    except Exception as e:
        print(f"错误: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def list_all_users():
    """列出所有用户及其角色"""
    try:
        conn = connect_db()
        cur = conn.cursor()
        
        users = cur.execute('SELECT id, username, role FROM user ORDER BY username').fetchall()
        
        print("\n当前系统用户列表:")
        print("-" * 40)
        print(f"{'ID':<5}{'用户名':<20}{'角色':<10}")
        print("-" * 40)
        
        for user in users:
            print(f"{user['id']:<5}{user['username']:<20}{user['role']:<10}")
        
        print("-" * 40)
        
    except Exception as e:
        print(f"获取用户列表失败: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # 显示所有用户
    list_all_users()
    
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("\n使用方法: python set_admin.py <用户名>")
        print("示例: python set_admin.py kevin")
        sys.exit(1)
    
    username = sys.argv[1]
    set_user_as_admin(username)
    
    # 再次显示用户列表以确认更改
    list_all_users() 