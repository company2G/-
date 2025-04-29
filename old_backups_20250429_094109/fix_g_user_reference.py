#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复g.user.id引用问题
"""

import os
import re
import sys

# 文件路径
APP_FILE = 'app_simple.py'
BACKUP_FILE = 'app_simple.py.user_fix_backup'

def backup_file(file_path, backup_path):
    """创建文件备份"""
    try:
        with open(file_path, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        print(f"已创建备份: {backup_path}")
        return True
    except Exception as e:
        print(f"创建备份失败: {str(e)}")
        return False

def fix_g_user_references():
    """修复对g.user.id的不安全引用"""
    try:
        if not os.path.exists(APP_FILE):
            print(f"错误: 找不到文件 {APP_FILE}")
            return False
            
        # 创建备份
        if not backup_file(APP_FILE, BACKUP_FILE):
            return False
            
        with open(APP_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找并替换不安全的g.user.id引用
        # 针对balance_transaction中的g.user.id引用
        pattern1 = r'(after_balance, g\.user\.id,)'
        replacement1 = r'after_balance, (g.user.id if hasattr(g, "user") and g.user is not None else 1),'
        
        # 针对operation_record中的g.user.id引用
        pattern2 = r'(g\.user\.id, \'添加产品\')'
        replacement2 = r'(g.user.id if hasattr(g, "user") and g.user is not None else 1), \'添加产品\''
        
        # 应用第一个替换
        new_content = re.sub(pattern1, replacement1, content)
        # 应用第二个替换
        new_content = re.sub(pattern2, replacement2, new_content)
        
        # 如果内容没有改变，可能需要更精确的模式匹配
        if new_content == content:
            print("警告: 没有发现g.user.id的不安全引用，或者替换模式不匹配。")
            print("尝试手动检查以下行:")
            
            # 查找可能的g.user.id引用
            g_user_lines = []
            for i, line in enumerate(content.splitlines()):
                if "g.user.id" in line and "if hasattr(g, 'user')" not in line:
                    g_user_lines.append((i+1, line.strip()))
            
            for line_num, line in g_user_lines:
                print(f"行 {line_num}: {line}")
                
            return False
        
        # 写入修改后的内容
        with open(APP_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"已修复 {APP_FILE} 中对g.user.id的不安全引用")
        return True
    except Exception as e:
        print(f"修复g.user.id引用时出错: {str(e)}")
        return False

def manual_fix():
    """手动修复指定的代码块"""
    try:
        if not os.path.exists(APP_FILE):
            print(f"错误: 找不到文件 {APP_FILE}")
            return False
            
        # 创建备份
        if not backup_file(APP_FILE, BACKUP_FILE):
            return False
            
        with open(APP_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 寻找并修复balance_transaction中的g.user.id引用
        balance_fixed = False
        operation_fixed = False
        
        for i in range(len(lines)):
            # 修复balance_transaction中的g.user.id引用
            if "INSERT INTO balance_transaction" in lines[i] and not balance_fixed:
                # 向前查找g.user.id行
                for j in range(i, min(i+15, len(lines))):
                    if "g.user.id" in lines[j] and "after_balance" in lines[j]:
                        # 替换行
                        lines[j] = lines[j].replace("g.user.id", "(g.user.id if hasattr(g, 'user') and g.user is not None else 1)")
                        balance_fixed = True
                        print(f"已修复balance_transaction中的g.user.id引用，行 {j+1}")
                        break
            
            # 修复operation_record中的g.user.id引用
            if "INSERT INTO operation_record" in lines[i] and not operation_fixed:
                # 向前查找g.user.id行
                for j in range(i, min(i+15, len(lines))):
                    if "g.user.id" in lines[j] and "添加产品" in lines[j]:
                        # 替换行
                        lines[j] = lines[j].replace("g.user.id", "(g.user.id if hasattr(g, 'user') and g.user is not None else 1)")
                        operation_fixed = True
                        print(f"已修复operation_record中的g.user.id引用，行 {j+1}")
                        break
                        
            # 如果两处都已修复，可以跳出循环
            if balance_fixed and operation_fixed:
                break
        
        # 写入修改后的内容
        with open(APP_FILE, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        if balance_fixed or operation_fixed:
            print(f"已修复 {APP_FILE} 中的g.user.id引用")
            return True
        else:
            print("未找到需要修复的g.user.id引用")
            return False
    except Exception as e:
        print(f"手动修复g.user.id引用时出错: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("g.user.id引用修复工具")
    print("=" * 60)
    
    # 先尝试正则表达式替换
    if not fix_g_user_references():
        print("自动修复失败，尝试手动修复...")
        if manual_fix():
            print("手动修复成功！")
        else:
            print("修复失败，请手动检查并修改代码。")
    else:
        print("修复成功！")
    
    print("=" * 60) 