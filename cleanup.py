#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
清理项目目录中的备份文件和临时修复脚本
"""

import os
import glob
import shutil
from datetime import datetime

# 创建备份文件夹，确保重要文件不会彻底丢失
backup_dir = "old_backups_" + datetime.now().strftime("%Y%m%d_%H%M%S")
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)
    print(f"已创建备份目录: {backup_dir}")

# 需要删除的文件模式
patterns = [
    # 备份文件
    "app_simple.py.bak*",
    "app_simple.py.fixed*",
    "app_simple_fixed*.py",
    "app_simple.py.*_bak",
    "app_simple.py.user_fix_backup",
    "appsimple.py.bak*",
    
    # 临时修复脚本
    "fix_*.py",
    "fix_*.cmd",
    "test_app.py",
    "direct_fix*.py"
]

# 统计文件数
total_files = 0
moved_files = 0

# 处理每种模式的文件
for pattern in patterns:
    matching_files = glob.glob(pattern)
    for file in matching_files:
        # 忽略清理脚本本身
        if file == __file__:
            continue
            
        total_files += 1
        
        # 移动到备份目录而不是直接删除
        try:
            shutil.move(file, os.path.join(backup_dir, file))
            moved_files += 1
            print(f"已移动: {file}")
        except Exception as e:
            print(f"移动 {file} 失败: {str(e)}")

# 汇总
if total_files == 0:
    print("没有找到需要清理的文件")
    # 删除空的备份目录
    try:
        os.rmdir(backup_dir)
    except:
        pass
else:
    print(f"\n清理完成! 共处理 {total_files} 个文件, 已移动 {moved_files} 个文件到 {backup_dir} 目录")
    print("如果确认不再需要这些备份，可以手动删除该目录") 