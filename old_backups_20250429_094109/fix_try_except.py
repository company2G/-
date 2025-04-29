#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
这个脚本用于修复app_simple.py文件中的嵌套try-except结构问题。
问题:
1. "获取详细使用记录"的try块嵌套在了"获取新增客户和归属统计"的try块内部，
   但没有单独的except块，这导致静态代码分析工具报错。
2. "获取最近的使用记录"也没有单独的except块。

修复方案:
1. 将"获取详细使用记录"和"获取最近的使用记录"部分从外层try块中移出
2. 为它们分别添加独立的try-except结构
3. 从原始try-except块的错误处理中移除detailed_usage和recent_usages的初始化
"""

def main():
    # 文件路径
    input_file = 'app_simple.py'
    output_file = 'app_simple_fixed.py'
    backup_file = 'app_simple.py.bak2'
    
    # 读取原始文件
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 创建备份
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已创建备份文件: {backup_file}")
    
    # -------------------------------------------
    # 修复1: 将"获取详细使用记录"部分从外层try块中移出
    # -------------------------------------------
    
    # 匹配第一部分：客户统计代码的结束和详细使用记录的开始
    pattern1 = r"(        # 更新creator_stats变量用于模板\n        creator_stats = attribution_stats\n\s+)(?=        # 获取详细使用记录)"
    replacement1 = r"\1    except Exception as e:\n        app.logger.error(f\"获取客户统计出错: {str(e)}\")\n        new_clients = []\n        attribution_stats = []\n        creator_stats = []\n    \n"
    
    # 应用第一次替换
    content = content.replace("        # 更新creator_stats变量用于模板\n        creator_stats = attribution_stats\n\n        # 获取详细使用记录", 
                              "        # 更新creator_stats变量用于模板\n        creator_stats = attribution_stats\n\n    except Exception as e:\n        app.logger.error(f\"获取客户统计出错: {str(e)}\")\n        new_clients = []\n        attribution_stats = []\n        creator_stats = []\n    \n    # 获取详细使用记录")
    
    # -------------------------------------------
    # 修复2: 修正"获取详细使用记录"部分的try缩进
    # -------------------------------------------
    content = content.replace("    # 获取详细使用记录\n        try:", 
                              "    # 获取详细使用记录\n    try:")
    
    # -------------------------------------------
    # 修复3: 将"获取最近使用记录"部分从嵌套结构中分离，并添加单独的except块
    # -------------------------------------------
    
    # 标记最近使用记录代码的开始和结束
    pattern3 = r"(            # 获取最近的使用记录.*?recent_usages = \[dict_from_row\(row\) for row in recent_usages\]\s+\n)(\s+except Exception as e:)"
    
    # 替换为独立的try-except结构
    content = content.replace("            # 获取最近的使用记录（不分组）", 
                              "    except Exception as e:\n        app.logger.error(f\"获取详细使用记录出错: {str(e)}\")\n        import traceback\n        traceback.print_exc()\n        detailed_usage = []\n    \n    # 获取最近的使用记录（不分组）\n    try:")
    
    # -------------------------------------------
    # 修复4: 修正"获取最近使用记录"部分的缩进
    # -------------------------------------------
    content = content.replace("    # 获取最近的使用记录（不分组）\n    try:\n            recent_usages_query", 
                              "    # 获取最近的使用记录（不分组）\n    try:\n        recent_usages_query")
    
    # -------------------------------------------
    # 修复5: 修正最近使用记录的代码缩进
    # -------------------------------------------
    lines = content.split('\n')
    start_idx = None
    end_idx = None
    
    # 查找需要修改缩进的代码块范围
    for i, line in enumerate(lines):
        if "# 获取最近的使用记录（不分组）" in line:
            start_idx = i
        elif start_idx is not None and "recent_usages = [dict_from_row(row)" in line:
            end_idx = i
            break
    
    # 如果找到了代码块，修正缩进
    if start_idx is not None and end_idx is not None:
        for i in range(start_idx + 2, end_idx + 1):  # +2 跳过try:行
            if lines[i].startswith("            "):
                lines[i] = "        " + lines[i][12:]  # 减少缩进
    
    # 重新组合内容
    content = '\n'.join(lines)
    
    # -------------------------------------------
    # 修复6: 添加最近使用记录的except块
    # -------------------------------------------
    pattern6 = r"(        recent_usages = \[dict_from_row\(row\) for row in recent_usages\]\s+\n)(\s+except Exception as e:)"
    replacement6 = r"\1\n    except Exception as e:\n        app.logger.error(f\"获取最近使用记录出错: {str(e)}\")\n        import traceback\n        traceback.print_exc()\n        recent_usages = []\n"
    
    # 应用替换
    content = content.replace("        recent_usages = [dict_from_row(row) for row in recent_usages]\n\n    except Exception as e:", 
                              "        recent_usages = [dict_from_row(row) for row in recent_usages]\n\n    except Exception as e:\n        app.logger.error(f\"获取最近使用记录出错: {str(e)}\")\n        import traceback\n        traceback.print_exc()\n        recent_usages = []\n\n    # 获取产品添加统计\n    try:")
    
    # -------------------------------------------
    # 修复7: 修正原始except块中的错误处理
    # -------------------------------------------
    content = content.replace("app.logger.error(f\"获取客户统计出错: {str(e)}\")\n        new_clients = []\n        attribution_stats = []\n        detailed_usage = []\n        recent_usages = []", 
                              "app.logger.error(f\"获取客户统计出错: {str(e)}\")\n        new_clients = []\n        attribution_stats = []")
    
    # -------------------------------------------
    # 修复8: 删除重复的"获取产品添加统计"代码
    # -------------------------------------------
    content = content.replace("    # 获取产品添加统计\n    try:\n        app.logger.error(f\"获取客户统计出错: {str(e)}\")\n        new_clients = []\n        attribution_stats = []\n    \n    # 获取产品添加统计", 
                              "    # 获取产品添加统计")
    
    # 保存修复后的文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"修复已完成并保存到: {output_file}")
    print("请检查修复后的文件是否正确，然后再替换原始文件。")

if __name__ == "__main__":
    main() 