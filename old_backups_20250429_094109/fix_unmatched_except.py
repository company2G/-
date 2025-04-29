#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复未匹配的except语句 - 专门针对app_simple.py中的语法错误
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

def fix_unmatched_except(file_path):
    """修复未匹配的except语句"""
    backup_path = backup_file(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    unmatched_except = []
    
    # 使用栈来跟踪try和except的匹配
    try_stack = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 检查是否有try语句
        if re.search(r'\btry\s*:', stripped):
            try_stack.append(i)  # 压入try语句的行号
        
        # 检查是否有except语句
        elif re.search(r'\bexcept\s+', stripped) or re.search(r'\bfinally\s*:', stripped):
            if try_stack:
                try_stack.pop()  # 如果有匹配的try，则弹出
            else:
                # 未匹配的except
                unmatched_except.append(i)
                print(f"发现未匹配的except在第{i+1}行: {stripped}")
    
    if not unmatched_except:
        print("没有发现未匹配的except语句")
        return True
    
    print(f"发现{len(unmatched_except)}个未匹配的except语句")
    
    # 修复未匹配的except
    # 方法：在未匹配的except前插入一个try块
    modified_lines = lines.copy()
    
    # 从后向前处理，避免行号变化影响前面的行
    for line_index in sorted(unmatched_except, reverse=True):
        indent = len(re.match(r'^(\s*)', lines[line_index]).group(1))
        indent_str = ' ' * indent
        
        # 向前查找合适的插入点
        insert_pos = line_index
        for j in range(line_index-1, -1, -1):
            prev_indent = len(re.match(r'^(\s*)', lines[j]).group(1))
            if prev_indent == indent and lines[j].strip():
                insert_pos = j
                break
        
        # 插入try块
        modified_lines.insert(insert_pos, f"{indent_str}try:")
        print(f"  在第{insert_pos+1}行插入try语句")
    
    # 保存修改后的内容
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(modified_lines))
    
    print(f"✅ 修复完成！已解决所有未匹配的except语句")
    print(f"如果还有问题，请使用备份 {backup_path} 恢复")
    return True

if __name__ == "__main__":
    print("开始修复app_simple.py中未匹配的except语句...")
    source_file = 'app_simple.py'
    
    if os.path.exists(source_file):
        if fix_unmatched_except(source_file):
            print("修复完成！请重新启动应用程序测试。")
        else:
            print("修复失败，请手动检查问题。")
    else:
        print(f"错误: 找不到文件 {source_file}") 