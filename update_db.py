#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库更新脚本 - 添加储值卡相关字段到现有数据库
"""

import os
import sqlite3
import sys

def get_db_connection():
    """获取数据库连接"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def check_columns_exist():
    """检查储值卡相关列是否已存在"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取client_product表的列信息
    cursor.execute("PRAGMA table_info(client_product)")
    columns = {row['name'] for row in cursor.fetchall()}
    
    # 检查需要添加的列
    missing_columns = []
    for column in ['payment_method', 'discount_rate', 'original_price', 'actual_paid']:
        if column not in columns:
            missing_columns.append(column)
    
    conn.close()
    return missing_columns

def check_client_columns():
    """检查客户表是否有余额和折扣率列"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取client表的列信息
    cursor.execute("PRAGMA table_info(client)")
    columns = {row['name'] for row in cursor.fetchall()}
    
    # 检查需要添加的列
    missing_columns = []
    for column in ['balance', 'discount']:
        if column not in columns:
            missing_columns.append(column)
    
    conn.close()
    return missing_columns

def add_missing_columns(missing_columns):
    """添加缺失的列到client_product表"""
    if not missing_columns:
        print("所有必要的列都已存在于client_product表中，无需更新。")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 定义列的默认值和类型
    column_definitions = {
        'payment_method': "TEXT DEFAULT 'cash'",  # 默认为现金支付
        'discount_rate': "REAL DEFAULT 1.0",      # 默认无折扣
        'original_price': "REAL",                 # 原始价格
        'actual_paid': "REAL"                     # 实际支付金额
    }
    
    # 添加缺失的列
    for column in missing_columns:
        try:
            sql = f"ALTER TABLE client_product ADD COLUMN {column} {column_definitions[column]}"
            cursor.execute(sql)
            print(f"成功添加列: {column}")
        except Exception as e:
            print(f"添加列 {column} 时出错: {str(e)}")
    
    conn.commit()
    conn.close()

def add_client_columns(missing_columns):
    """添加缺失的列到client表"""
    if not missing_columns:
        print("所有必要的列都已存在于client表中，无需更新。")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 定义列的默认值和类型
    column_definitions = {
        'balance': "REAL DEFAULT 0.0",   # 默认余额为0
        'discount': "REAL DEFAULT 1.0"   # 默认折扣率为1.0（无折扣）
    }
    
    # 添加缺失的列
    for column in missing_columns:
        try:
            sql = f"ALTER TABLE client ADD COLUMN {column} {column_definitions[column]}"
            cursor.execute(sql)
            print(f"成功添加列: {column}")
        except Exception as e:
            print(f"添加列 {column} 时出错: {str(e)}")
    
    conn.commit()
    conn.close()

def create_balance_transaction_table():
    """创建余额交易记录表，如果不存在"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='balance_transaction'")
    if cursor.fetchone():
        print("余额交易记录表已存在，无需创建。")
    else:
        # 创建余额交易记录表
        sql = """
        CREATE TABLE balance_transaction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            transaction_type TEXT NOT NULL,
            description TEXT,
            before_balance REAL NOT NULL,
            after_balance REAL NOT NULL,
            operator_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES client (id),
            FOREIGN KEY (operator_id) REFERENCES user (id)
        )
        """
        try:
            cursor.execute(sql)
            print("成功创建余额交易记录表。")
        except Exception as e:
            print(f"创建余额交易记录表时出错: {str(e)}")
    
    conn.commit()
    conn.close()

def main():
    """主函数"""
    print("=" * 50)
    print("禾燃客户管理系统 - 数据库更新工具")
    print("=" * 50)
    print("正在检查数据库结构...")
    
    # 检查并添加client_product表的列
    missing_columns = check_columns_exist()
    if missing_columns:
        print(f"client_product表缺少以下列: {', '.join(missing_columns)}")
        add_missing_columns(missing_columns)
    else:
        print("client_product表结构正常。")
    
    # 检查并添加client表的列
    missing_client_columns = check_client_columns()
    if missing_client_columns:
        print(f"client表缺少以下列: {', '.join(missing_client_columns)}")
        add_client_columns(missing_client_columns)
    else:
        print("client表结构正常。")
    
    # 创建余额交易记录表
    create_balance_transaction_table()
    
    print("=" * 50)
    print("数据库更新完成！")
    print("=" * 50)

if __name__ == "__main__":
    main() 