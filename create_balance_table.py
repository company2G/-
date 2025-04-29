#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
添加余额管理相关表到数据库
"""

import os
import sqlite3

# 数据库路径
db_path = 'database.db'

# 检查数据库文件是否存在
if not os.path.exists(db_path):
    print(f"错误: 数据库文件 {db_path} 不存在!")
    exit(1)

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查表是否已存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='balance_transaction'")
if cursor.fetchone():
    print("表 balance_transaction 已存在，无需创建。")
else:
    # 创建余额交易记录表
    print("正在创建 balance_transaction 表...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS balance_transaction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        amount REAL NOT NULL,  -- 正数表示充值，负数表示消费
        transaction_type TEXT NOT NULL,  -- 'recharge'充值，'purchase'消费，'refund'退款
        description TEXT,
        before_balance REAL,
        after_balance REAL,
        operator_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES client (id),
        FOREIGN KEY (operator_id) REFERENCES user (id)
    )
    ''')
    print("表 balance_transaction 创建成功!")

# 检查客户表是否有balance和discount字段
cursor.execute("PRAGMA table_info(client)")
client_columns = [column[1] for column in cursor.fetchall()]

if 'balance' not in client_columns:
    print("正在向client表添加balance字段...")
    cursor.execute("ALTER TABLE client ADD COLUMN balance REAL DEFAULT 0.0")
    print("字段 balance 添加成功!")

if 'discount' not in client_columns:
    print("正在向client表添加discount字段...")
    cursor.execute("ALTER TABLE client ADD COLUMN discount REAL DEFAULT 1.0")
    print("字段 discount 添加成功!")

# 提交更改
conn.commit()
conn.close()

print("数据库迁移完成!") 