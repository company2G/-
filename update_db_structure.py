#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库结构更新脚本
- 将client_product表中的remaining_sessions列重命名为remaining_count
"""

import sqlite3
import os
import sys
import time
import datetime

def backup_database(db_path):
    """备份数据库"""
    backup_path = db_path + '.backup_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    print(f"正在备份数据库到: {backup_path}")
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print("数据库备份成功")
        return True
    except Exception as e:
        print(f"数据库备份失败: {str(e)}")
        return False

def update_db_structure(db_path):
    """更新数据库结构"""
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        return False
    
    # 备份数据库
    if not backup_database(db_path):
        print("由于备份失败，取消更新")
        return False
    
    print("开始更新数据库结构...")
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        
        # 查询client_product表结构
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(client_product)")
        columns = cursor.fetchall()
        
        has_remaining_sessions = any(col[1] == 'remaining_sessions' for col in columns)
        has_remaining_count = any(col[1] == 'remaining_count' for col in columns)
        
        if has_remaining_count:
            print("列 'remaining_count' 已经存在，不需要更新")
            return True
        
        if not has_remaining_sessions:
            print("列 'remaining_sessions' 不存在，无法更新")
            return False
        
        # 创建临时表
        print("创建临时表...")
        conn.executescript('''
            -- 创建新的临时表
            CREATE TABLE client_product_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                purchase_date TEXT,
                start_date TEXT,
                remaining_count INTEGER,
                expiry_date TEXT,
                status TEXT CHECK(status IN ('active', 'expired', 'used_up')),
                notes TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                payment_method TEXT DEFAULT 'cash',
                discount_rate REAL DEFAULT 1.0,
                original_price REAL,
                actual_paid REAL,
                FOREIGN KEY (client_id) REFERENCES client (id),
                FOREIGN KEY (product_id) REFERENCES product (id)
            );
            
            -- 复制数据
            INSERT INTO client_product_temp (
                id, client_id, product_id, purchase_date, start_date, 
                remaining_count, expiry_date, status, notes, created_at, 
                updated_at, payment_method, discount_rate, original_price, actual_paid
            )
            SELECT 
                id, client_id, product_id, purchase_date, start_date, 
                remaining_sessions, expiry_date, status, notes, created_at, 
                updated_at, payment_method, discount_rate, original_price, actual_paid 
            FROM client_product;
            
            -- 删除旧表
            DROP TABLE client_product;
            
            -- 重命名新表
            ALTER TABLE client_product_temp RENAME TO client_product;
        ''')
        
        print("数据库更新成功")
        return True
        
    except Exception as e:
        print(f"更新数据库时出错: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # 确定数据库路径
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
    
    print(f"准备更新数据库: {db_path}")
    print("此操作将会更新数据库结构，请确保您已备份数据库。")
    print("更新内容: 将client_product表中的remaining_sessions列重命名为remaining_count")
    
    confirm = input("是否继续? (y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        sys.exit(0)
    
    if update_db_structure(db_path):
        print("数据库结构更新完成")
    else:
        print("数据库结构更新失败")
        sys.exit(1) 