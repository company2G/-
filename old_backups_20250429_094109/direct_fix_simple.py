#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
直接修复脚本：修复app_simple.py中嵌套try-except结构问题
"""

import os
import time

def backup_file(file_path):
    """创建文件备份"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.bak_{timestamp}"
    with open(file_path, 'r', encoding='utf-8') as src:
        content = src.read()
    with open(backup_path, 'w', encoding='utf-8') as dst:
        dst.write(content)
    print(f"✅ 已创建备份: {backup_path}")
    return True

def fix_nested_try():
    """简单直接地修复app_simple.py文件中没有except块的try语句"""
    source_file = 'app_simple.py'
    
    # 先创建备份
    backup_file(source_file)
    
    # 读取文件内容
    with open(source_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修复策略: 在最外层try的结尾添加except块，同时在内层try前添加结束标记
    # 1. 找到外层try的开始位置
    outer_try_start = -1
    for i, line in enumerate(lines):
        if "# 获取新增客户和归属统计" in line and "try:" in lines[i+1]:
            outer_try_start = i + 1
            break
    
    if outer_try_start == -1:
        print("❌ 无法找到外层try语句")
        return False
    
    # 2. 找到第一个嵌套try (获取详细使用记录)
    nested_try1_start = -1
    for i in range(outer_try_start + 1, len(lines)):
        if "# 获取详细使用记录" in lines[i] and "try:" in lines[i+1]:
            nested_try1_start = i + 1
            break
    
    if nested_try1_start == -1:
        print("❌ 无法找到第一个嵌套try语句")
        return False
    
    # 3. 获取缩进级别
    indent = ""
    for char in lines[outer_try_start]:
        if char == ' ' or char == '\t':
            indent += char
        else:
            break
    
    # 4. 在第一个嵌套try前添加外层try的结束和内层try的开始
    # 获取前一行的内容（用于保持连续性）
    prev_line = lines[nested_try1_start - 2]  # -2因为-1是注释行
    
    # 构建修改内容
    fix_content = []
    fix_content.append(prev_line)  # 保持前一行不变
    fix_content.append(f"{indent}except Exception as e:\n")
    fix_content.append(f"{indent}    app.logger.error(f\"获取客户统计出错: {{str(e)}}\")\n")
    fix_content.append(f"{indent}    new_clients = []\n")
    fix_content.append(f"{indent}    attribution_stats = []\n")
    fix_content.append(f"{indent}    creator_stats = []\n")
    fix_content.append(f"\n")
    fix_content.append(lines[nested_try1_start - 1])  # 添加注释行
    
    # 替换原有内容
    lines[nested_try1_start - 2:nested_try1_start] = fix_content
    
    # 5. 找到第二个嵌套try（获取最近的使用记录）
    nested_try2_start = -1
    # 由于我们插入了新行，需要重新计算行号
    offset = len(fix_content) - 2  # 我们替换了两行，增加了len(fix_content)行，所以偏移是len(fix_content)-2
    
    for i in range(nested_try1_start + offset, len(lines)):
        if "# 获取最近的使用记录" in lines[i]:
            nested_try2_start = i
            break
    
    # 6. 在第二个嵌套try前添加第一个嵌套try的结束块
    if nested_try2_start != -1:
        # 构建第一个嵌套try的except块
        fix_content2 = []
        fix_content2.append(f"{indent}except Exception as e:\n")
        fix_content2.append(f"{indent}    app.logger.error(f\"获取详细使用记录出错: {{str(e)}}\")\n")
        fix_content2.append(f"{indent}    import traceback\n")
        fix_content2.append(f"{indent}    traceback.print_exc()\n")
        fix_content2.append(f"{indent}    detailed_usage = []\n")
        fix_content2.append(f"\n")
        
        # 插入这个except块
        lines.insert(nested_try2_start, "\n")
        for i, line in enumerate(fix_content2):
            lines.insert(nested_try2_start + i, line)
        
        # 更新偏移
        offset += len(fix_content2) + 1
    
    # 7. 找到"获取产品添加统计"注释
    stats_comment_start = -1
    for i in range(nested_try2_start + 1, len(lines)):
        if "# 获取产品添加统计" in lines[i]:
            stats_comment_start = i
            break
    
    # 8. 在"获取产品添加统计"前添加第二个嵌套try的结束块
    if stats_comment_start != -1:
        # 构建第二个嵌套try的except块
        fix_content3 = []
        fix_content3.append(f"{indent}except Exception as e:\n")
        fix_content3.append(f"{indent}    app.logger.error(f\"获取最近使用记录出错: {{str(e)}}\")\n")
        fix_content3.append(f"{indent}    import traceback\n")
        fix_content3.append(f"{indent}    traceback.print_exc()\n")
        fix_content3.append(f"{indent}    recent_usages = []\n")
        fix_content3.append(f"\n")
        
        # 插入这个except块
        lines.insert(stats_comment_start, "\n")
        for i, line in enumerate(fix_content3):
            lines.insert(stats_comment_start + i, line)
    
    # 9. 保存修改后的文件
    with open(source_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ 修复成功！已解决嵌套try-except结构问题")
    return True

if __name__ == "__main__":
    print("开始直接修复app_simple.py中的嵌套try-except结构问题...")
    if fix_nested_try():
        print("修复完成！请重新启动应用程序测试。")
    else:
        print("修复失败，请手动检查问题。") 