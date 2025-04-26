import os
import re

def fix_app_simple():
    # 读取app_simple.py文件
    with open('app_simple.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建备份
    with open('app_simple.py.bak', 'w', encoding='utf-8') as f:
        f.write(content)
    print("创建了app_simple.py的备份")
    
    # 替换字段名
    updated_content = content.replace('remaining_amount', 'remaining_count')
    
    # 写回文件
    with open('app_simple.py', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("已将app_simple.py中的'remaining_amount'替换为'remaining_count'")
    print("如果替换后出现问题，可以使用备份文件恢复")

if __name__ == "__main__":
    fix_app_simple()