#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库优化工具 - 禾燃客户管理系统
为关键表添加索引以提高查询性能
"""

import os
import sys
import logging
import sqlite3
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('db_optimize.log')
    ]
)
logger = logging.getLogger('db_optimize')

def get_db_path():
    """获取数据库文件路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'database.db')

def create_connection():
    """创建到SQLite数据库的连接"""
    try:
        conn = sqlite3.connect(get_db_path())
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        logger.error(f"数据库连接错误: {e}")
        return None

def get_table_info(cursor, table_name):
    """获取表的字段信息"""
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]  # 返回字段名列表
    except sqlite3.Error as e:
        logger.error(f"获取表 {table_name} 结构时出错: {e}")
        return []

def check_table_exists(cursor, table_name):
    """检查表是否存在"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def create_indexes():
    """为数据库表创建索引以优化查询性能"""
    conn = create_connection()
    if conn is None:
        return False
    
    cursor = conn.cursor()
    
    # 首先获取实际存在的表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    logger.info(f"数据库中存在的表: {', '.join(existing_tables)}")
    
    # 索引定义 - 根据实际表结构定义
    indexes = []
    
    # 客户表索引 (client)
    if 'client' in existing_tables:
        fields = get_table_info(cursor, 'client')
        if 'name' in fields:
            indexes.append(('client', 'idx_client_name', ['name'], False))
        if 'phone' in fields:
            indexes.append(('client', 'idx_client_phone', ['phone'], True))
        if 'created_at' in fields:
            indexes.append(('client', 'idx_client_created_at', ['created_at'], False))
    
    # 产品表索引 (product)
    if 'product' in existing_tables:
        fields = get_table_info(cursor, 'product')
        if 'name' in fields:
            indexes.append(('product', 'idx_product_name', ['name'], False))
        if 'type' in fields:
            indexes.append(('product', 'idx_product_type', ['type'], False))
    
    # 客户产品表索引 (client_product)
    if 'client_product' in existing_tables:
        fields = get_table_info(cursor, 'client_product')
        if 'client_id' in fields:
            indexes.append(('client_product', 'idx_client_product_client_id', ['client_id'], False))
        if 'product_id' in fields:
            indexes.append(('client_product', 'idx_client_product_product_id', ['product_id'], False))
        if 'purchase_date' in fields:
            indexes.append(('client_product', 'idx_client_product_purchase_date', ['purchase_date'], False))
    
    # 预约表索引 (appointment)
    if 'appointment' in existing_tables:
        fields = get_table_info(cursor, 'appointment')
        if 'client_id' in fields:
            indexes.append(('appointment', 'idx_appointment_client_id', ['client_id'], False))
        if 'appointment_date' in fields:
            indexes.append(('appointment', 'idx_appointment_date', ['appointment_date'], False))
        if 'status' in fields:
            indexes.append(('appointment', 'idx_appointment_status', ['status'], False))
    
    # 用户表索引 (user)
    if 'user' in existing_tables:
        fields = get_table_info(cursor, 'user')
        if 'username' in fields:
            indexes.append(('user', 'idx_user_username', ['username'], True))
        if 'role' in fields:
            indexes.append(('user', 'idx_user_role', ['role'], False))
    
    # 报表记录表索引 (report_records)
    if 'report_records' in existing_tables:
        fields = get_table_info(cursor, 'report_records')
        if 'user_id' in fields:
            indexes.append(('report_records', 'idx_report_records_user_id', ['user_id'], False))
        if 'status' in fields:
            indexes.append(('report_records', 'idx_report_records_status', ['status'], False))
    
    # 通知日志表索引 (notification_logs)
    if 'notification_logs' in existing_tables:
        fields = get_table_info(cursor, 'notification_logs')
        if 'client_id' in fields:
            indexes.append(('notification_logs', 'idx_notification_logs_client_id', ['client_id'], False))
        if 'appointment_id' in fields:
            indexes.append(('notification_logs', 'idx_notification_logs_appointment_id', ['appointment_id'], False))
    
    # 体重记录表索引 (weight_record)
    if 'weight_record' in existing_tables:
        fields = get_table_info(cursor, 'weight_record')
        if 'client_id' in fields:
            indexes.append(('weight_record', 'idx_weight_record_client_id', ['client_id'], False))
        if 'record_date' in fields:
            indexes.append(('weight_record', 'idx_weight_record_date', ['record_date'], False))
    
    # 异步任务表索引 (async_tasks)
    if 'async_tasks' in existing_tables:
        fields = get_table_info(cursor, 'async_tasks')
        if 'task_id' in fields:
            indexes.append(('async_tasks', 'idx_async_tasks_task_id', ['task_id'], True))
        if 'status' in fields:
            indexes.append(('async_tasks', 'idx_async_tasks_status', ['status'], False))
    
    # 创建所有索引
    created_count = 0
    skipped_count = 0
    for table, index_name, columns, is_unique in indexes:
        try:
            # 检查索引是否已存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'")
            if cursor.fetchone() is None:
                unique_str = "UNIQUE" if is_unique else ""
                columns_str = ", ".join(columns)
                sql = f"CREATE {unique_str} INDEX {index_name} ON {table} ({columns_str})"
                cursor.execute(sql)
                logger.info(f"已创建索引: {index_name} 在表 {table} 上")
                created_count += 1
            else:
                logger.info(f"索引 {index_name} 已存在，跳过")
                skipped_count += 1
        except sqlite3.Error as e:
            logger.error(f"创建索引 {index_name} 时出错: {e}")
    
    conn.commit()
    
    # 执行ANALYZE来更新统计信息
    try:
        cursor.execute("ANALYZE")
        logger.info("已执行ANALYZE命令更新统计信息")
    except sqlite3.Error as e:
        logger.error(f"执行ANALYZE命令时出错: {e}")
    
    conn.close()
    logger.info(f"索引创建完成：共创建 {created_count} 个索引，跳过 {skipped_count} 个已存在索引")
    return True

def vacuum_database():
    """执行VACUUM操作以优化数据库文件大小"""
    conn = create_connection()
    if conn is None:
        return False
    
    cursor = conn.cursor()
    try:
        cursor.execute("VACUUM")
        logger.info("已执行VACUUM命令优化数据库文件大小")
    except sqlite3.Error as e:
        logger.error(f"执行VACUUM命令时出错: {e}")
    
    conn.close()
    return True

def optimize_database():
    """执行所有数据库优化操作"""
    logger.info("开始数据库优化...")
    
    # 创建索引
    if create_indexes():
        logger.info("索引创建操作完成")
    else:
        logger.error("索引创建操作失败")
    
    # 执行VACUUM
    if vacuum_database():
        logger.info("数据库VACUUM操作成功")
    else:
        logger.error("数据库VACUUM操作失败")
    
    logger.info("数据库优化完成")
    return True

if __name__ == "__main__":
    db_path = get_db_path()
    logger.info(f"使用数据库: {db_path}")
    
    if not os.path.exists(db_path):
        logger.error(f"数据库文件不存在: {db_path}")
        sys.exit(1)
    
    start_time = datetime.now()
    logger.info(f"数据库优化开始于: {start_time}")
    
    success = optimize_database()
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"数据库优化结束于: {end_time}, 总耗时: {duration}")
    
    if success:
        logger.info("数据库优化成功完成")
        sys.exit(0)
    else:
        logger.error("数据库优化过程中发生错误")
        sys.exit(1) 