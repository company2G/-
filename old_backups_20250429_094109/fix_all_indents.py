#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复app_simple.py文件中的所有缩进问题
"""

import re

# 读取文件内容
with open('app_simple.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# 修复第1210-1215行的缩进问题
if len(lines) >= 1215:
    # 针对第1212行的db.commit()
    if 'db.commit()' in lines[1211]:
        indent_level = re.match(r'^(\s*)', lines[1211]).group(1)
        if len(indent_level) > 8:  # 如果缩进过多
            lines[1211] = '        db.commit()\n'
    
    # 针对第1214-1215行
    if 'flash' in lines[1213] and 'return' in lines[1214]:
        lines[1213] = '        flash(\'客户信息已更新成功\', \'success\')\n'
        lines[1214] = '        return redirect(url_for(\'view_client\', client_id=client_id))\n'

# 写入修改后的文件
with open('app_simple.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("已修复app_simple.py中的缩进问题") 