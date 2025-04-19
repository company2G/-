#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重置用户会话并强制更新admin权限的脚本
"""

import os
import sys
import sqlite3
from datetime import datetime
import shutil

# 获取数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def connect_db():
    """连接到数据库"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def reset_admin_user(username="kevin"):
    """重置管理员用户权限"""
    try:
        # 备份数据库
        backup_path = DB_PATH + '.backup'
        shutil.copy2(DB_PATH, backup_path)
        print(f"数据库已备份至: {backup_path}")
        
        # 连接数据库
        conn = connect_db()
        cur = conn.cursor()
        
        # 检查用户是否存在
        user = cur.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        
        if not user:
            print(f"错误: 用户 '{username}' 不存在")
            return False
        
        # 1. 确保用户角色为admin
        cur.execute('UPDATE user SET role = ? WHERE username = ?', ('admin', username))
        
        # 2. 确保client_id为NULL
        cur.execute('UPDATE user SET client_id = NULL WHERE username = ?', (username,))
        
        # 3. 尝试重置密码(如果需要)
        reset_password = input("是否重置密码? (y/n): ").lower()
        if reset_password == 'y':
            new_password = input("请输入新密码(留空则使用默认密码'admin'): ")
            if not new_password:
                new_password = "admin"
            
            # 导入密码哈希函数
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(new_password)
            
            cur.execute('UPDATE user SET password_hash = ? WHERE username = ?', 
                        (password_hash, username))
            print(f"密码已重置为: {new_password}")
        
        # 提交更改
        conn.commit()
        
        print(f"\n成功: 用户 '{username}' 已重置为管理员权限")
        return True
        
    except Exception as e:
        print(f"错误: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def clear_flask_sessions():
    """尝试清除Flask session文件"""
    try:
        flask_session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
        if os.path.exists(flask_session_dir):
            for file in os.listdir(flask_session_dir):
                file_path = os.path.join(flask_session_dir, file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            print("Flask会话缓存已清除")
        else:
            print("未找到Flask会话目录")
    except Exception as e:
        print(f"清除会话缓存失败: {str(e)}")

if __name__ == "__main__":
    print("禾燃客户管理系统 - 管理员权限重置工具")
    print("=" * 50)
    
    username = "kevin"  # 默认用户
    if len(sys.argv) > 1:
        username = sys.argv[1]
    
    print(f"正在为用户 '{username}' 重置管理员权限...")
    
    if reset_admin_user(username):
        # 尝试清除会话
        clear_flask_sessions()
        
        print("\n操作完成。请按照以下步骤操作:")
        print("1. 重启Flask应用 (关闭并重新运行)")
        print("2. 完全清除浏览器缓存和Cookie")
        print("3. 重新登录系统")
        print("\n如果仍有问题，请查看以下可能的原因:")
        print("- 检查app_simple.py中admin_required装饰器的实现")
        print("- 检查User类中is_admin属性的计算逻辑")
        print("- 检查是否有其他代码干扰了权限检查")
    else:
        print("权限重置失败，请检查错误信息") 