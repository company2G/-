#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接修复预约管理路由问题的脚本
"""

import os
import sys
import re
import shutil
import sqlite3

# 应用文件路径
APP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_simple.py')
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def connect_db():
    """连接到数据库"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")
        return None

def backup_app_file():
    """备份应用文件"""
    try:
        backup_path = APP_FILE + '.bak'
        shutil.copy2(APP_FILE, backup_path)
        print(f"应用文件已备份至: {backup_path}")
        return True
    except Exception as e:
        print(f"备份文件失败: {str(e)}")
        return False

def ensure_admin_permissions():
    """确保用户有管理员权限"""
    try:
        conn = connect_db()
        if not conn:
            return False
            
        cur = conn.cursor()
        
        # 修复可能错误的管理员角色
        cur.execute("UPDATE user SET role = 'admin' WHERE role LIKE 'admin%' AND role != 'admin'")
        
        # 确保至少有一个管理员用户
        admin_count = cur.execute("SELECT COUNT(*) FROM user WHERE role = 'admin'").fetchone()[0]
        
        if admin_count == 0:
            # 将用户名为kevin的用户设为管理员
            kevin = cur.execute("SELECT * FROM user WHERE username = 'kevin'").fetchone()
            if kevin:
                cur.execute("UPDATE user SET role = 'admin' WHERE username = 'kevin'")
                print("已将用户 'kevin' 设置为管理员")
            else:
                # 将第一个找到的用户设置为管理员
                first_user = cur.execute("SELECT * FROM user LIMIT 1").fetchone()
                if first_user:
                    cur.execute("UPDATE user SET role = 'admin' WHERE id = ?", (first_user['id'],))
                    print(f"已将用户 '{first_user['username']}' 设置为管理员")
                else:
                    print("警告: 系统中没有用户，无法设置管理员")
        
        # 确保admin用户的client_id为NULL
        cur.execute("UPDATE user SET client_id = NULL WHERE role = 'admin'")
        
        conn.commit()
        print("用户权限设置已更新")
        return True
    except Exception as e:
        print(f"更新用户权限失败: {str(e)}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def direct_fix_routes():
    """直接修复预约管理路由"""
    try:
        with open(APP_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加可能缺失的导入
        missing_imports = []
        
        if 'redirect' not in content[:1000]:
            missing_imports.append('redirect')
        if 'url_for' not in content[:1000]:
            missing_imports.append('url_for')
            
        if missing_imports:
            # 检查是否有现有的flask导入
            import_match = re.search(r'from flask import (.*?)\n', content)
            if import_match:
                imports = import_match.group(1)
                new_imports = imports
                for imp in missing_imports:
                    if imp not in imports:
                        new_imports += f", {imp}"
                content = content.replace(imports, new_imports)
                print(f"已添加缺失的导入: {', '.join(missing_imports)}")
            else:
                # 添加新的导入语句
                import_line = f"from flask import {', '.join(missing_imports)}\n"
                first_import = content.find('import')
                if first_import > 0:
                    content = content[:first_import] + import_line + content[first_import:]
                    print(f"已添加缺失的导入: {', '.join(missing_imports)}")
        
        # 检查是否已存在/manage_appointments路由
        manage_route_exists = False
        admin_manage_route_exists = False
        
        manage_route_match = re.search(r'@app\.route\([\'"]\/manage_appointments[\'"]\)', content)
        if manage_route_match:
            manage_route_exists = True
            print("已存在/manage_appointments路由")
            
        admin_route_match = re.search(r'@app\.route\([\'"]\/admin_manage_appointments[\'"]\)', content)
        if admin_route_match:
            admin_manage_route_exists = True
            print("已存在/admin_manage_appointments路由")
        
        # 检查是否有admin_manage_appointments函数
        admin_func_match = re.search(r'def\s+admin_manage_appointments\s*\(\)', content)
        admin_func_exists = bool(admin_func_match)
        
        # 检查是否有manage_appointments函数
        manage_func_match = re.search(r'def\s+manage_appointments\s*\(\)', content)
        manage_func_exists = bool(manage_func_match)
        
        changes_made = False
        
        # 处理路由和函数的各种情况
        if admin_manage_route_exists and admin_func_exists:
            # 理想情况，检查是否需要添加兼容路由
            if not manage_route_exists:
                # 添加兼容性路由
                redirect_route = """
@app.route('/manage_appointments')
@login_required
@admin_required
def manage_appointments_redirect():
    \"\"\"预约管理页面的兼容性重定向\"\"\"
    return redirect(url_for('admin_manage_appointments'))
"""
                # 找一个合适的位置添加路由
                pos = content.find('@app.route')
                if pos > 0:
                    insert_pos = content.find('\n', pos)
                    if insert_pos > 0:
                        content = content[:insert_pos] + redirect_route + content[insert_pos:]
                        changes_made = True
                        print("已添加兼容性重定向路由")
        
        elif manage_route_exists and manage_func_exists and not admin_manage_route_exists:
            # 只有manage_appointments路由和函数，重命名为admin_manage_appointments
            content = content.replace('def manage_appointments()', 'def admin_manage_appointments()')
            content = content.replace("@app.route('/manage_appointments')", "@app.route('/admin_manage_appointments')")
            
            # 添加兼容性路由
            redirect_route = """
@app.route('/manage_appointments')
@login_required
@admin_required
def manage_appointments_redirect():
    \"\"\"预约管理页面的兼容性重定向\"\"\"
    return redirect(url_for('admin_manage_appointments'))
"""
            # 找一个合适的位置添加路由
            pos = content.find('@app.route')
            if pos > 0:
                insert_pos = content.find('\n', pos)
                if insert_pos > 0:
                    content = content[:insert_pos] + redirect_route + content[insert_pos:]
                    changes_made = True
                    print("已重命名函数并添加兼容性重定向")
        
        elif not admin_manage_route_exists and not manage_route_exists:
            # 没有任何预约管理路由，添加一个基本实现
            basic_implementation = """
@app.route('/admin_manage_appointments')
@login_required
@admin_required
def admin_manage_appointments():
    \"\"\"管理员预约管理页面\"\"\"
    # 获取各种状态的预约
    db = get_db()
    pending_appointments = db.execute(
        'SELECT a.*, c.name as client_name, c.phone as client_phone, p.name as service_name '
        'FROM appointment a '
        'LEFT JOIN client c ON a.client_id = c.id '
        'LEFT JOIN product p ON a.product_id = p.id '
        'WHERE a.status = "pending" '
        'ORDER BY a.appointment_time DESC'
    ).fetchall()
    
    confirmed_appointments = db.execute(
        'SELECT a.*, c.name as client_name, c.phone as client_phone, p.name as service_name '
        'FROM appointment a '
        'LEFT JOIN client c ON a.client_id = c.id '
        'LEFT JOIN product p ON a.product_id = p.id '
        'WHERE a.status = "confirmed" '
        'ORDER BY a.appointment_time DESC'
    ).fetchall()
    
    completed_appointments = db.execute(
        'SELECT a.*, c.name as client_name, c.phone as client_phone, p.name as service_name '
        'FROM appointment a '
        'LEFT JOIN client c ON a.client_id = c.id '
        'LEFT JOIN product p ON a.product_id = p.id '
        'WHERE a.status = "completed" '
        'ORDER BY a.appointment_time DESC'
    ).fetchall()
    
    cancelled_appointments = db.execute(
        'SELECT a.*, c.name as client_name, c.phone as client_phone, p.name as service_name '
        'FROM appointment a '
        'LEFT JOIN client c ON a.client_id = c.id '
        'LEFT JOIN product p ON a.product_id = p.id '
        'WHERE a.status = "cancelled" '
        'ORDER BY a.appointment_time DESC'
    ).fetchall()
    
    return render_template('manage_appointments.html', 
                           pending_appointments=pending_appointments,
                           confirmed_appointments=confirmed_appointments,
                           completed_appointments=completed_appointments, 
                           cancelled_appointments=cancelled_appointments)

@app.route('/manage_appointments')
@login_required
@admin_required
def manage_appointments_redirect():
    \"\"\"预约管理页面的兼容性重定向\"\"\"
    return redirect(url_for('admin_manage_appointments'))
"""
            # 确保导入了render_template
            if 'render_template' not in content[:1000]:
                import_match = re.search(r'from flask import (.*?)\n', content)
                if import_match:
                    imports = import_match.group(1)
                    if 'render_template' not in imports:
                        new_imports = imports + ', render_template'
                        content = content.replace(imports, new_imports)
            
            # 找一个合适的位置添加实现
            route_sections = re.findall(r'@app\.route.*?def.*?\(\).*?return.*?[^\n]', content, re.DOTALL)
            if route_sections:
                last_section = route_sections[-1]
                content = content.replace(last_section, last_section + '\n' + basic_implementation)
                changes_made = True
                print("已添加基本预约管理功能")
            else:
                print("警告: 未找到合适的位置添加路由")
        
        # 更新模板中的链接
        templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        base_template = os.path.join(templates_dir, 'base.html')
        
        if os.path.exists(base_template):
            with open(base_template, 'r', encoding='utf-8') as f:
                base_content = f.read()
            
            # 检查模板中的预约管理链接
            if 'admin_manage_appointments' not in base_content and 'url_for(' in base_content:
                new_base_content = re.sub(
                    r'href="{{.*?url_for\([\'"]manage_appointments[\'"]\).*?}}"',
                    'href="{{ url_for(\'admin_manage_appointments\') }}"',
                    base_content
                )
                
                if new_base_content != base_content:
                    with open(base_template, 'w', encoding='utf-8') as f:
                        f.write(new_base_content)
                    print("已更新模板中的预约管理链接")
        
        # 保存修改
        if changes_made:
            with open(APP_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
            print("应用文件已更新")
        else:
            print("无需修改应用文件")
        
        return True
    except Exception as e:
        print(f"修复路由失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("禾燃客户管理系统 - 路由问题直接修复工具")
    print("=" * 50)
    
    # 备份应用文件
    if backup_app_file():
        # 确保用户权限设置
        ensure_admin_permissions()
        
        # 直接修复路由
        if direct_fix_routes():
            print("\n修复完成。请按照以下步骤操作:")
            print("1. 重启Flask应用")
            print("2. 使用下列URL访问预约管理页面:")
            print("   http://127.0.0.1:5000/admin_manage_appointments")
            print("   或 http://127.0.0.1:5000/manage_appointments")
            print("\n如果仍有问题，请将以下信息提供给支持人员:")
            print(f"- 应用文件路径: {APP_FILE}")
            print(f"- 数据库文件路径: {DB_PATH}")
            print(f"- 备份文件位置: {APP_FILE}.bak")
        else:
            print("\n修复过程中出现错误，请联系支持人员")
    else:
        print("无法创建备份，操作已取消") 