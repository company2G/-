#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能修复脚本：解决app_simple.py中嵌套try-except结构问题，同时保留函数结构
"""

import os
import re
import time
import traceback

def backup_file(file_path):
    """创建文件备份"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.bak_{timestamp}"
    try:
        with open(file_path, 'r', encoding='utf-8') as src:
            content = src.read()
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(content)
        print(f"✅ 已创建备份: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ 创建备份失败: {str(e)}")
        return False

def restore_from_backup(backup_path, target_file):
    """从备份恢复文件"""
    try:
        with open(backup_path, 'r', encoding='utf-8') as src:
            content = src.read()
        with open(target_file, 'w', encoding='utf-8') as dst:
            dst.write(content)
        print(f"✅ 已从备份恢复文件: {backup_path} -> {target_file}")
        return True
    except Exception as e:
        print(f"❌ 恢复文件失败: {str(e)}")
        return False

def fix_nested_try_except():
    """修复app_simple.py中的嵌套try-except结构"""
    source_file = 'app_simple.py'
    
    # 先备份
    if not backup_file(source_file):
        print("❌ 无法继续修复，请确保app_simple.py文件存在且可读写")
        return False
    
    try:
        # 读取文件为行列表，这样更容易保持原始函数结构
        with open(source_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 定位admin_statistics函数
        admin_stats_start = -1
        admin_stats_end = -1
        
        for i, line in enumerate(lines):
            if "@app.route('/admin/statistics')" in line:
                admin_stats_start = i
            if admin_stats_start > 0 and i > admin_stats_start:
                # 找到函数结束的标志（下一个函数的定义）
                if line.startswith('@app.route') or line.startswith('def ') and line[0] != ' ':
                    admin_stats_end = i - 1
                    break
        
        if admin_stats_start == -1:
            print("❌ 无法找到admin_statistics函数，请手动检查app_simple.py")
            return False
        
        if admin_stats_end == -1:
            # 如果没找到函数结束，假设是文件末尾
            admin_stats_end = len(lines) - 1
        
        # 获取函数正文部分
        func_body = lines[admin_stats_start:admin_stats_end+1]
        
        # 查找有问题的嵌套try-except结构
        nested_try_start = -1
        nested_try_end = -1
        
        for i, line in enumerate(func_body):
            if "# 获取新增客户和归属统计" in line and "try:" in func_body[i+1]:
                nested_try_start = i
            if nested_try_start > 0 and i > nested_try_start and "# 获取产品添加统计" in line:
                nested_try_end = i
                break
        
        if nested_try_start == -1 or nested_try_end == -1:
            print("❌ 无法找到需要修复的嵌套try-except结构")
            return False
        
        # 提取需要修改的部分
        nested_try_block = func_body[nested_try_start:nested_try_end]
        
        # 确定缩进级别 - 使用第一行的缩进作为基准
        indent = ""
        for char in nested_try_block[0]:
            if char == ' ' or char == '\t':
                indent += char
            else:
                break
        
        # 分析嵌套try块的内部结构
        client_stats_end = -1
        details_usage_start = -1
        recent_usage_start = -1
        
        for i, line in enumerate(nested_try_block):
            if "# 获取详细使用记录" in line:
                details_usage_start = i
                client_stats_end = i - 1  # 客户统计结束于详细使用记录前一行
            if "# 获取最近的使用记录" in line:
                recent_usage_start = i
        
        if client_stats_end == -1 or details_usage_start == -1 or recent_usage_start == -1:
            print("❌ 无法分析嵌套try-except的结构，请手动检查")
            return False
        
        # 构建修复后的代码块
        fixed_block = []
        
        # 1. 客户统计部分（保持原样，但添加自己的except块）
        fixed_block.extend(nested_try_block[:client_stats_end+1])
        fixed_block.append(f"{indent}except Exception as e:\n")
        fixed_block.append(f"{indent}    app.logger.error(f\"获取客户统计出错: {{str(e)}}\")\n")
        fixed_block.append(f"{indent}    new_clients = []\n")
        fixed_block.append(f"{indent}    attribution_stats = []\n")
        fixed_block.append(f"{indent}    creator_stats = []\n")
        fixed_block.append(f"\n")
        
        # 2. 详细使用记录部分
        fixed_block.append(f"{indent}# 获取详细使用记录\n")
        fixed_block.append(f"{indent}try:\n")
        
        # 提取详细使用记录的内容部分（排除注释行）
        for i in range(details_usage_start+1, recent_usage_start):
            if "try:" in nested_try_block[i]:
                continue  # 跳过原来的try行
            if "# 获取最近" in nested_try_block[i]:
                break
            # 保持缩进一致性
            line = nested_try_block[i]
            if line.startswith(indent + "    "):  # 原来多了一级缩进
                line = indent + line.lstrip()
            fixed_block.append(line)
        
        # 为详细使用记录添加except块
        fixed_block.append(f"{indent}except Exception as e:\n")
        fixed_block.append(f"{indent}    app.logger.error(f\"获取详细使用记录出错: {{str(e)}}\")\n")
        fixed_block.append(f"{indent}    import traceback\n")
        fixed_block.append(f"{indent}    traceback.print_exc()\n")
        fixed_block.append(f"{indent}    detailed_usage = []\n")
        fixed_block.append(f"\n")
        
        # 3. 最近使用记录部分
        fixed_block.append(f"{indent}# 获取最近的使用记录（不分组）\n")
        fixed_block.append(f"{indent}try:\n")
        
        # 提取最近使用记录的内容（排除注释行和try行）
        for i in range(recent_usage_start+1, len(nested_try_block)):
            if "try:" in nested_try_block[i]:
                continue  # 跳过原来的try行
            if "# 获取产品添加统计" in nested_try_block[i]:
                break
            # 保持缩进一致性
            line = nested_try_block[i]
            if line.startswith(indent + "    "):  # 原来多了一级缩进
                line = indent + line.lstrip()
            fixed_block.append(line)
        
        # 为最近使用记录添加except块
        fixed_block.append(f"{indent}except Exception as e:\n")
        fixed_block.append(f"{indent}    app.logger.error(f\"获取最近使用记录出错: {{str(e)}}\")\n")
        fixed_block.append(f"{indent}    import traceback\n")
        fixed_block.append(f"{indent}    traceback.print_exc()\n")
        fixed_block.append(f"{indent}    recent_usages = []\n")
        fixed_block.append(f"\n")
        
        # 加上获取产品添加统计的注释行
        fixed_block.append(f"{indent}# 获取产品添加统计\n")
        
        # 替换原先的嵌套try-except块
        func_body[nested_try_start:nested_try_end] = fixed_block
        
        # 替换整个函数体
        lines[admin_stats_start:admin_stats_end+1] = func_body
        
        # 保存修复后的文件
        with open(source_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ 修复成功！已修复app_simple.py中的嵌套try-except结构问题，并保留了函数结构")
        return True
        
    except Exception as e:
        print(f"❌ 修复过程中出错: {str(e)}")
        traceback.print_exc()
        
        # 如果出错，恢复到最新的备份
        backups = [f for f in os.listdir() if f.startswith('app_simple.py.bak_')]
        if backups:
            latest_backup = sorted(backups)[-1]
            restore_from_backup(latest_backup, source_file)
        return False

if __name__ == "__main__":
    print("开始智能修复app_simple.py中的嵌套try-except结构问题...")
    if fix_nested_try_except():
        print("修复完成！请重新启动应用程序测试。")
    else:
        print("修复失败，已恢复备份。请手动检查问题。") 