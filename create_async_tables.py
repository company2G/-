#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建异步任务所需的数据库表 - 禾燃客户管理系统
"""

import os
import sqlite3

def get_db_path():
    """获取数据库文件路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'database.db')

def create_async_tables():
    """创建异步任务所需的数据库表"""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件 {db_path} 不存在")
        return False
    
    conn = sqlite3.connect(db_path)
    
    try:
        # 创建报表记录表
        conn.executescript('''
        -- 创建报表记录表
        CREATE TABLE IF NOT EXISTS report_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            report_type TEXT NOT NULL,
            task_id TEXT,
            file_path TEXT,
            status TEXT NOT NULL,
            error_message TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );
        
        -- 创建通知日志表
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            appointment_id INTEGER,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES client (id),
            FOREIGN KEY (appointment_id) REFERENCES appointment (id)
        );
        
        -- 创建客户设置表
        CREATE TABLE IF NOT EXISTS client_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER UNIQUE NOT NULL,
            notification_type TEXT DEFAULT 'sms',
            FOREIGN KEY (client_id) REFERENCES client (id)
        );
        
        -- 创建异步任务记录表
        CREATE TABLE IF NOT EXISTS async_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE,
            task_type TEXT NOT NULL,
            status TEXT NOT NULL,
            params TEXT,
            result TEXT,
            error_message TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT
        );
        ''')
        
        conn.commit()
        print("异步任务相关数据库表创建成功")
        return True
        
    except Exception as e:
        print(f"创建数据库表时出错: {str(e)}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    create_async_tables() 