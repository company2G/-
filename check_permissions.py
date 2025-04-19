#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查用户权限和显示管理员链接状态
"""

import os
import sys
import sqlite3
import re

# 获取数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
APP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_simple.py')

def check_db_users():
    """检查数据库中的用户权限"""
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # 获取所有用户
        users = cur.execute('SELECT id, username, role, client_id FROM user ORDER BY id').fetchall()
        
        print("\n==== 数据库用户列表 ====")
        print(f"{'ID':<5}{'用户名':<15}{'角色':<10}{'客户ID':<10}")
        print("-" * 40)
        
        for user in users:
            print(f"{user['id']:<5}{user['username']:<15}{user['role']:<10}{user['client_id'] or 'NULL':<10}")
        
        # 检查管理员用户
        admin_users = [user for user in users if user['role'] == 'admin']
        if admin_users:
            print("\n系统中的管理员用户:")
            for admin in admin_users:
                print(f"- {admin['username']} (ID: {admin['id']})")
        else:
            print("\n警告: 系统中没有管理员用户!")
        
        # 直接更新kevin为管理员
        kevin = cur.execute("SELECT * FROM user WHERE username = 'kevin'").fetchone()
        if kevin:
            if kevin['role'] != 'admin':
                cur.execute("UPDATE user SET role = 'admin', client_id = NULL WHERE username = 'kevin'")
                conn.commit()
                print("\n已将用户 'kevin' 设置为管理员")
            else:
                print("\n用户 'kevin' 已是管理员")
        
        conn.close()
    except Exception as e:
        print(f"检查数据库失败: {str(e)}")

def check_app_routes():
    """检查应用中的路由定义"""
    try:
        with open(APP_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n==== 路由检查 ====")
        
        # 检查预约管理路由
        manage_route = re.search(r'@app\.route\([\'"]\/manage_appointments[\'"]\)', content)
        admin_route = re.search(r'@app\.route\([\'"]\/admin_manage_appointments[\'"]\)', content)
        
        if manage_route:
            print("✓ 找到 /manage_appointments 路由")
        else:
            print("✗ 未找到 /manage_appointments 路由")
        
        if admin_route:
            print("✓ 找到 /admin_manage_appointments 路由")
        else:
            print("✗ 未找到 /admin_manage_appointments 路由")
        
        # 检查admin_required装饰器
        decorator = re.search(r'def admin_required\(view\):(.*?)return wrapped_view', content, re.DOTALL)
        if decorator:
            print("✓ 找到 admin_required 装饰器")
            
            # 检查装饰器实现是否正确
            decorator_code = decorator.group(0)
            if 'role' in decorator_code and 'admin' in decorator_code:
                print("✓ 装饰器检查用户角色")
            else:
                print("✗ 装饰器可能没有正确检查用户角色")
        else:
            print("✗ 未找到 admin_required 装饰器")
        
        # 检查User类
        user_class = re.search(r'class User\(UserMixin\):(.*?)# 用户加载函数', content, re.DOTALL)
        if user_class:
            print("✓ 找到 User 类")
            
            # 检查is_admin属性
            is_admin = re.search(r'self\.is_admin\s*=\s*(.*?)\n', user_class.group(1))
            if is_admin:
                admin_code = is_admin.group(1)
                print(f"✓ is_admin属性设置: {admin_code}")
                
                if "role == 'admin'" in admin_code:
                    print("✓ is_admin检查用户角色正确")
                else:
                    print("✗ is_admin可能没有正确检查角色")
            else:
                print("✗ 未找到 is_admin 属性设置")
        else:
            print("✗ 未找到 User 类")
    except Exception as e:
        print(f"检查应用代码失败: {str(e)}")

def check_templates():
    """检查模板中的链接"""
    try:
        templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        base_template = os.path.join(templates_dir, 'base.html')
        
        if os.path.exists(base_template):
            with open(base_template, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print("\n==== 模板检查 ====")
            
            # 检查导航菜单
            admin_menu = re.search(r'{%\s*if\s+current_user\.is_admin\s*%}(.*?){%\s*endif\s*%}', content, re.DOTALL)
            if admin_menu:
                print("✓ 找到管理员菜单条件")
                
                # 检查预约管理链接
                appointments_link = re.search(r'href="{{.*?url_for\([\'"]([a-zA-Z0-9_]+)[\'"]\).*?}}"[^>]*>预约管理</a>', content)
                if appointments_link:
                    route_name = appointments_link.group(1)
                    print(f"✓ 预约管理链接使用路由: {route_name}")
                    
                    if route_name != 'admin_manage_appointments':
                        print(f"✗ 预约管理链接应使用 'admin_manage_appointments' 而非 '{route_name}'")
                else:
                    print("✗ 未找到预约管理链接")
            else:
                print("✗ 未找到管理员菜单条件")
        else:
            print(f"未找到模板文件: {base_template}")
    except Exception as e:
        print(f"检查模板失败: {str(e)}")

if __name__ == "__main__":
    print("禾燃客户管理系统 - 权限检查工具")
    print("=" * 50)
    
    # 检查数据库用户
    check_db_users()
    
    # 检查应用路由
    check_app_routes()
    
    # 检查模板
    check_templates()
    
    print("\n==== 总结 ====")
    print("1. 如果未发现管理员用户，脚本已尝试将'kevin'设置为管理员")
    print("2. 检查上面的报告，查看是否有红色✗标记的问题")
    print("3. 运行 direct_fix.py 脚本修复所有问题")
    print("4. 重启应用后尝试访问预约管理页面:")
    print("   http://127.0.0.1:5000/admin_manage_appointments") 