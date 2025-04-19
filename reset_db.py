#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
禾燃客户管理系统 - 重置数据库工具
"""

import os
import sqlite3
import shutil
import sys
from datetime import datetime

def reset_database():
    """重置数据库，删除现有数据库并重建"""
    # 获取工作目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'database.db')
    schema_path = os.path.join(script_dir, 'schema.sql')
    
    # 检查schema.sql是否存在
    if not os.path.exists(schema_path):
        print(f"错误: 未找到数据库模式文件 {schema_path}")
        return False
    
    # 如果存在旧数据库则备份
    if os.path.exists(db_path):
        backup_name = f'database.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        backup_path = os.path.join(script_dir, backup_name)
        
        try:
            shutil.copy2(db_path, backup_path)
            print(f"已将旧数据库备份到: {backup_path}")
            
            # 删除旧数据库
            os.remove(db_path)
            print("已删除旧数据库")
        except Exception as e:
            print(f"备份或删除旧数据库时出错: {str(e)}")
            return False
    
    # 创建新数据库
    try:
        conn = sqlite3.connect(db_path)
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        
        # 创建默认管理员账户
        from werkzeug.security import generate_password_hash
        password_hash = generate_password_hash('admin')
        
        conn.execute(
            'INSERT INTO user (username, password_hash, role) VALUES (?, ?, ?)',
            ('admin', password_hash, 'admin')
        )
        
        # 添加示例产品数据
        now = datetime.now().isoformat()
        conn.execute('''
            INSERT INTO product (name, price, description, type, category, sessions, validity_days, created_at, updated_at)
            VALUES 
            ('单次体验课', 99, '单次体验服务，了解我们的专业服务', 'count', '体验课程', 1, NULL, ?, ?),
            ('10次卡', 980, '10次专业服务，随时预约', 'count', '次数卡', 10, NULL, ?, ?),
            ('月卡', 1280, '30天内不限次数使用', 'period', '期限卡', NULL, 30, ?, ?),
            ('季卡', 3500, '90天内不限次数使用', 'period', '期限卡', NULL, 90, ?, ?)
        ''', (now, now, now, now, now, now, now, now))
        
        conn.commit()
        conn.close()
        
        print(f"成功创建新数据库: {db_path}")
        print("已创建默认管理员账户 (用户名: admin, 密码: admin)")
        print("已添加示例产品数据")
        return True
    except Exception as e:
        print(f"创建新数据库时出错: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 65)
    print("禾燃客户管理系统 - 数据库重置工具")
    print("=" * 65)
    
    # 确认重置
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        confirm = 'y'
    else:
        confirm = input("此操作将删除现有数据库并创建一个新的空数据库。所有数据将丢失！是否继续? (y/n): ")
    
    if confirm.lower() == 'y':
        if reset_database():
            print("\n✓ 数据库重置成功")
            print("\n您现在可以使用以下账户登录系统:")
            print("  用户名: admin")
            print("  密码: admin")
        else:
            print("\n✗ 数据库重置失败")
    else:
        print("\n操作已取消") 