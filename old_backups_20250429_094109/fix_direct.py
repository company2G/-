#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
直接修复app_simple.py中的语法错误 - 针对2875行附近的except缩进问题
"""

import os
import re
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
    return backup_path

def fix_direct(file_path):
    """直接修复特定行的缩进问题"""
    backup_path = backup_file(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 修复行2833-2879左右的except语句缩进问题
    # 通过直接搜索特定错误模式
    
    # 查找模式1: 不正确的except缩进
    for i in range(len(lines)):
        line = lines[i].rstrip()
        # 查找错误模式："except Exception as e:" 不在函数内部或与对应的try不对齐
        if re.match(r'^(\s*)except\s+Exception\s+as\s+e\s*:', line):
            indent = re.match(r'^(\s*)', line).group(1)
            
            # 向上查找对应的try语句
            for j in range(i-1, max(0, i-100), -1):
                if re.match(r'^' + re.escape(indent) + r'try\s*:', lines[j].rstrip()):
                    # 找到对应的try，不需要修复
                    break
            else:
                # 没有找到对应的try，这是一个需要修复的except
                print(f"发现需要修复的except在第{i+1}行: {line}")
                
                # 确定正确的缩进级别，查找上一个非空行
                correct_indent = ""
                for j in range(i-1, max(0, i-20), -1):
                    prev_line = lines[j].rstrip()
                    if prev_line and not prev_line.isspace():
                        # 获取上一行的缩进
                        correct_indent = re.match(r'^(\s*)', prev_line).group(1)
                        break
                
                # 插入缺失的try语句
                if correct_indent:
                    # 查找合适的插入点
                    insert_pos = i
                    for j in range(i-1, max(0, i-20), -1):
                        if re.match(r'^' + re.escape(correct_indent) + r'\S', lines[j].rstrip()):
                            insert_pos = j
                            break
                    
                    # 在适当位置插入try语句
                    lines.insert(insert_pos, f"{correct_indent}try:\n")
                    print(f"  在第{insert_pos+1}行插入try语句")
                    
                    # 因为插入了一行，当前except的行号需要加1
                    i += 1
    
    # 另一种常见的错误模式：缩进错误的except块
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        
        # 检查是否有"except Exception as e:"行，后续行缩进不正确
        match = re.match(r'^(\s*)except\s+Exception\s+as\s+e\s*:', line)
        if match:
            indent = match.group(1)
            expected_next_indent = indent + "    "  # 期望的下一行缩进
            
            # 检查下一行的缩进是否正确
            if i+1 < len(lines) and lines[i+1].strip():
                next_indent = re.match(r'^(\s*)', lines[i+1]).group(1)
                if next_indent != expected_next_indent:
                    # 缩进不正确，修复这个块
                    print(f"发现缩进错误的except块，从第{i+1}行开始")
                    
                    # 修复后续行的缩进，直到遇到相同或更小缩进的行
                    j = i + 1
                    while j < len(lines) and (not lines[j].strip() or len(re.match(r'^(\s*)', lines[j]).group(1)) > len(indent)):
                        if lines[j].strip():  # 跳过空行
                            content = lines[j].lstrip()
                            lines[j] = expected_next_indent + content
                        j += 1
                    
                    print(f"  修复了从第{i+2}到第{j}行的缩进")
        i += 1
    
    # 保存修改后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ 修复完成！请测试应用程序")
    print(f"如果还有问题，请使用备份 {backup_path} 恢复")
    return True

if __name__ == "__main__":
    print("开始直接修复app_simple.py中的缩进问题...")
    source_file = 'app_simple.py'
    
    if os.path.exists(source_file):
        if fix_direct(source_file):
            print("修复完成！请重新启动应用程序测试。")
        else:
            print("修复失败，请手动检查问题。")
    else:
        print(f"错误: 找不到文件 {source_file}") 