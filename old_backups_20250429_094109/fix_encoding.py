#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 修复app_simple.py中的编码和缩进问题
import re

# 读取文件内容
with open('app_simple.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# 修复第540行附近的问题
# 1. 修复中文注释
content = content.replace('浠庤〃鍗曡幏鍙栨暟鎹?', '从表单获取数据')
content = content.replace('楗涔犳儻', '饮食习惯')
content = content.replace('韬綋鐘跺喌', '身体状况')
content = content.replace('浣撻噸鐩稿叧', '体重相关')
content = content.replace('鍏宠仈鎿嶄綔鍛', '关联操作员')
content = content.replace('楠岃瘉鏁版嵁', '验证数据')

# 2. 修复缩进问题（确保所有缩进使用4个空格）
def fix_indentation(text):
    lines = text.split('\n')
    fixed_lines = []
    
    for line in lines:
        # 检测行首的空白字符
        leading_spaces = len(line) - len(line.lstrip())
        
        # 如果这行是缩进的，确保缩进级别是4的倍数
        if leading_spaces > 0:
            # 计算应该有多少个缩进级别
            indent_level = (leading_spaces + 2) // 4  # +2是为了向上取整
            fixed_line = ' ' * (indent_level * 4) + line.lstrip()
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

# 修复 add_client 函数的缩进
# 查找函数范围
match = re.search(r'@app\.route\(\'/client/add\'.*?\ndef add_client\(\):.*?return render_template\(\'add_client\.html\', operators=operators\)', content, re.DOTALL)
if match:
    function_text = match.group(0)
    fixed_function = fix_indentation(function_text)
    content = content.replace(function_text, fixed_function)

# 写回文件
with open('app_simple.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("文件修复完成！") 