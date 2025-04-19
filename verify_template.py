#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证模板中的权限检查
"""

import os
import sys
import re
import glob

def check_templates():
    """检查所有模板中的权限检查语句"""
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    
    print(f"正在检查目录: {templates_dir}")
    
    # 获取所有HTML模板
    templates = glob.glob(os.path.join(templates_dir, '*.html'))
    print(f"找到 {len(templates)} 个模板文件")
    
    for template_path in templates:
        template_name = os.path.basename(template_path)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查权限条件
            admin_checks = []
            
            # 检查 current_user.is_admin
            is_admin_matches = re.findall(r'{%\s*if\s+current_user\.is_admin\s*%}', content)
            if is_admin_matches:
                admin_checks.append(f"current_user.is_admin 检查: {len(is_admin_matches)} 处")
            
            # 检查 is_admin 模板变量
            var_admin_matches = re.findall(r'{%\s*if\s+is_admin\s*%}', content)
            if var_admin_matches:
                admin_checks.append(f"is_admin 变量检查: {len(var_admin_matches)} 处")
            
            # 检查其他可能的管理员检查方式
            other_admin_matches = re.findall(r'{%\s*if\s+.*admin.*\s*%}', content)
            other_count = len(other_admin_matches) - len(is_admin_matches) - len(var_admin_matches)
            if other_count > 0:
                admin_checks.append(f"其他admin相关检查: {other_count} 处")
            
            if admin_checks:
                print(f"\n文件: {template_name}")
                print("-" * 40)
                for check in admin_checks:
                    print(f"- {check}")
            
        except Exception as e:
            print(f"处理 {template_name} 时出错: {str(e)}")

if __name__ == "__main__":
    print("禾燃客户管理系统 - 模板权限检查工具")
    print("=" * 50)
    
    check_templates() 