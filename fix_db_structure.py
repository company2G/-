#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
禾燃客户管理系统 - 数据库结构修复工具
"""

import os
import sqlite3
import sys

def fix_user_table():
    """修复user表结构，添加缺失的列"""
    # 获取工作目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'database.db')
    
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在 {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取user表结构
        cursor.execute("PRAGMA table_info(user)")
        existing_columns = {column['name']: column['type'] for column in cursor.fetchall()}
        
        print(f"当前user表结构: {existing_columns}")
        
        # 需要确保存在的列
        needed_columns = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'username': 'TEXT UNIQUE NOT NULL',
            'password_hash': 'TEXT NOT NULL',
            'role': 'TEXT NOT NULL',
            'client_id': 'INTEGER',
            'name': 'TEXT',
            'phone': 'TEXT',
            'email': 'TEXT',
            'created_at': 'TIMESTAMP',
            'last_login': 'TIMESTAMP'
        }
        
        # 检查并添加缺失的列
        columns_added = 0
        for col_name, col_type in needed_columns.items():
            if col_name not in existing_columns and col_name != 'id':  # 主键不能添加
                try:
                    cursor.execute(f'ALTER TABLE user ADD COLUMN {col_name} {col_type}')
                    print(f"已添加列: {col_name} ({col_type})")
                    columns_added += 1
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"列 {col_name} 已存在")
                    else:
                        print(f"添加列 {col_name} 时出错: {str(e)}")
        
        conn.commit()
        
        if columns_added > 0:
            print(f"\n成功添加了 {columns_added} 个列到user表")
        else:
            print("\nuser表结构已完整，无需修改")
        
        # 检查user表中的记录数
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        print(f"user表中有 {user_count} 条记录")
        
        # 关闭连接
        conn.close()
        return True
    except Exception as e:
        print(f"修复user表时出错: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 65)
    print("禾燃客户管理系统 - 数据库结构修复工具")
    print("=" * 65)
    
    # 确认修复
    confirm = input("此操作将修复数据库表结构。是否继续? (y/n): ")
    
    if confirm.lower() == 'y':
        if fix_user_table():
            print("\n✓ 数据库表结构修复成功")
        else:
            print("\n✗ 数据库表结构修复失败")
    else:
        print("\n操作已取消") 