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

def fix_nested_try_except():
    """修复app_simple.py文件中的嵌套try-except结构问题"""
    
    # 读取原始文件
    with open('app_simple.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并修复嵌套的try-except结构
    pattern = r'(# 更新creator_stats变量用于模板\s+creator_stats = attribution_stats\s+)\s+(# 获取详细使用记录\s+try:)'
    replacement = r'\1\n    except Exception as e:\n        app.logger.error(f"获取客户统计出错: {str(e)}")\n        new_clients = []\n        attribution_stats = []\n        creator_stats = []\n    \n    \2'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # 查找最后一个try块（获取最近使用记录）
    pattern2 = r'(# 获取最近的使用记录.*?recent_usages = \[dict_from_row\(row\) for row in recent_usages\]\s+)\s+except Exception as e:'
    replacement2 = r'\1\n    except Exception as e:\n        app.logger.error(f"获取最近使用记录出错: {str(e)}")\n        import traceback\n        traceback.print_exc()\n        recent_usages = []\n    \n    # 获取产品添加统计\n    try:'
    
    new_content = re.sub(pattern2, replacement2, new_content, flags=re.DOTALL)
    
    # 替换原始try-except中的错误处理（把详细使用记录和最近使用记录从错误处理中移除）
    pattern3 = r'app\.logger\.error\(f"获取客户统计出错: \{str\(e\)\}"\)\s+new_clients = \[\]\s+attribution_stats = \[\]\s+detailed_usage = \[\]\s+recent_usages = \[\]'
    replacement3 = r'app.logger.error(f"获取客户统计出错: {str(e)}")\n        new_clients = []\n        attribution_stats = []'
    
    new_content = re.sub(pattern3, replacement3, new_content, flags=re.DOTALL)
    
    # 保存修复后的文件
    with open('app_simple_fixed.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("文件已修复并保存为 app_simple_fixed.py")

if __name__ == "__main__":
    fix_app_simple()
    fix_nested_try_except()