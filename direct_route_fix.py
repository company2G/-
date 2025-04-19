#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接修复路由冲突问题，无需用户交互
"""

import os
import sys
import re
import shutil

# 应用文件路径
APP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_simple.py')

def backup_app_file():
    """备份应用文件"""
    backup_path = APP_FILE + '.bak.' + str(int(__import__('time').time()))
    shutil.copy2(APP_FILE, backup_path)
    print(f"应用文件已备份至: {backup_path}")
    return backup_path

def direct_fix_route_conflict():
    """直接修复路由冲突问题，不依赖正则表达式模式匹配"""
    try:
        with open(APP_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 寻找包含manage_appointments和admin_manage_appointments的行
        route_lines = []
        for i, line in enumerate(lines):
            if '@app.route' in line and ('manage_appointments' in line or 'admin_manage_appointments' in line):
                route_lines.append((i, line))
        
        if len(route_lines) <= 1:
            print(f"未找到路由冲突，仅发现 {len(route_lines)} 个相关路由定义。")
            return False
        
        print(f"找到 {len(route_lines)} 个可能冲突的路由定义:")
        for i, (line_num, line) in enumerate(route_lines):
            print(f"{i+1}. 第 {line_num+1} 行: {line.strip()}")
        
        # 查找admin_manage_appointments函数
        admin_func_line = -1
        for i, line in enumerate(lines):
            if 'def admin_manage_appointments(' in line:
                admin_func_line = i
                break
        
        if admin_func_line == -1:
            print("未找到admin_manage_appointments函数定义。")
            return False
        
        print(f"找到admin_manage_appointments函数在第 {admin_func_line+1} 行")
        
        # 查找函数的装饰器
        decorator_start = admin_func_line
        while decorator_start > 0 and '@' in lines[decorator_start-1]:
            decorator_start -= 1
        
        decorators = lines[decorator_start:admin_func_line]
        print(f"找到 {len(decorators)} 个装饰器:")
        for dec in decorators:
            print(f"- {dec.strip()}")
        
        # 查找是否有多个路由装饰器
        route_decorators = [d for d in decorators if '@app.route' in d]
        if len(route_decorators) <= 1:
            print("未找到多个路由装饰器，可能问题在其他位置。")
            
            # 检查是否有其他函数使用了相同的端点名称
            other_func_route = None
            for i, line in enumerate(lines):
                if i != admin_func_line and 'def admin_manage_appointments(' in line:
                    # 找到另一个同名函数
                    other_func_route = i
                    break
            
            if other_func_route is not None:
                print(f"发现另一个同名函数在第 {other_func_route+1} 行!")
                
                # 重命名这个函数和引用
                other_func_start = other_func_route
                while other_func_start > 0 and '@' in lines[other_func_start-1]:
                    other_func_start -= 1
                
                # 重命名为admin_manage_appointments_alt
                lines[other_func_route] = lines[other_func_route].replace('def admin_manage_appointments(', 'def admin_manage_appointments_alt(')
                print(f"已将第 {other_func_route+1} 行的函数重命名为admin_manage_appointments_alt")
                
                # 更新模板中的引用
                templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
                if os.path.exists(templates_dir):
                    for filename in os.listdir(templates_dir):
                        if filename.endswith('.html'):
                            template_path = os.path.join(templates_dir, filename)
                            try:
                                with open(template_path, 'r', encoding='utf-8') as f:
                                    template_content = f.read()
                                
                                if 'admin_manage_appointments' in template_content:
                                    print(f"在模板 {filename} 中找到引用，但不修改模板文件")
                            except Exception as e:
                                print(f"读取模板 {filename} 失败: {e}")
            else:
                # 检查是否有两个相同路径的路由
                route_paths = {}
                for i, line in enumerate(lines):
                    if '@app.route' in line:
                        # 提取路径
                        path_match = re.search(r'@app\.route\([\'"](.+?)[\'"]\)', line)
                        if path_match:
                            path = path_match.group(1)
                            if path in route_paths:
                                print(f"发现重复的路由路径 '{path}':")
                                print(f"- 第 {route_paths[path]+1} 行: {lines[route_paths[path]].strip()}")
                                print(f"- 第 {i+1} 行: {line.strip()}")
                                
                                # 找到这个路由对应的函数
                                func_line = i + 1
                                while func_line < len(lines) and 'def ' not in lines[func_line]:
                                    func_line += 1
                                
                                if func_line < len(lines) and 'def ' in lines[func_line]:
                                    func_name = re.search(r'def\s+(\w+)\(', lines[func_line])
                                    if func_name:
                                        print(f"路由 '{path}' 对应的函数: {func_name.group(1)}")
                                        
                                        # 重命名后一个函数以避免冲突
                                        new_func_name = func_name.group(1) + '_alt'
                                        lines[func_line] = lines[func_line].replace(func_name.group(1), new_func_name)
                                        print(f"已将第 {func_line+1} 行的函数重命名为 {new_func_name}")
                            else:
                                route_paths[path] = i
        
        # 应用最简单的修复方法：合并路由装饰器
        print("\n应用通用修复方法：合并路由装饰器...")
        
        # 在admin_manage_appointments函数前找到所有装饰器
        decorators = []
        current_line = admin_func_line - 1
        while current_line >= 0 and '@' in lines[current_line]:
            decorators.insert(0, lines[current_line])
            current_line -= 1
        
        # 分离路由装饰器和其他装饰器
        route_decorators = []
        other_decorators = []
        
        for dec in decorators:
            if '@app.route' in dec:
                route_decorators.append(dec)
            else:
                other_decorators.append(dec)
        
        # 创建新的装饰器组合
        new_decorators = []
        for route in route_decorators:
            # 提取路径部分
            path_match = re.search(r'@app\.route\([\'"](.+?)[\'"](.*?)\)', route)
            if path_match:
                path = path_match.group(1)
                options = path_match.group(2)
                new_decorators.append(f"@app.route('{path}'{options})\n")
        
        # 确保只保留唯一的路由
        unique_decorators = []
        seen_paths = set()
        for dec in new_decorators:
            path_match = re.search(r'@app\.route\([\'"](.+?)[\'"](.*?)\)', dec)
            if path_match:
                path = path_match.group(1)
                if path not in seen_paths:
                    seen_paths.add(path)
                    unique_decorators.append(dec)
        
        # 添加其他非路由装饰器
        for dec in other_decorators:
            if dec not in unique_decorators:
                unique_decorators.append(dec)
        
        # 检查是否有变化
        original_decorators = ''.join(decorators)
        new_decorator_str = ''.join(unique_decorators)
        
        if original_decorators == new_decorator_str:
            print("装饰器没有变化，尝试另一种方法...")
            
            # 直接删除第二个路由装饰器
            if len(route_decorators) > 1:
                # 保留第一个路由，删除其他
                new_lines = []
                added_route = False
                for i, line in enumerate(lines):
                    if i >= decorator_start and i < admin_func_line:
                        if '@app.route' in line:
                            if not added_route:
                                new_lines.append(line)
                                added_route = True
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)
                
                lines = new_lines
                print("已删除多余的路由装饰器")
        else:
            # 替换装饰器
            new_lines = lines[:current_line+1]
            new_lines.extend(unique_decorators)
            new_lines.extend(lines[admin_func_line:])
            
            lines = new_lines
            print("已合并路由装饰器")
        
        # 写入修复后的内容
        with open(APP_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return True
    except Exception as e:
        print(f"修复路由冲突失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("禾燃客户管理系统 - 路由冲突直接修复工具")
    print("=" * 50)
    
    # 备份应用文件
    backup_path = backup_app_file()
    
    print("\n开始修复...")
    
    # 直接修复路由冲突
    if direct_fix_route_conflict():
        print("\n修复完成! 已解决路由冲突问题。")
        print("\n请按照以下步骤操作:")
        print("1. 重启Flask应用")
        print("2. 使用以下URL访问预约管理页面:")
        print("   http://127.0.0.1:5000/admin_manage_appointments")
        print("\n如果仍有问题，可以还原备份:", backup_path)
    else:
        print("\n修复失败，请手动检查应用代码或还原备份:", backup_path) 