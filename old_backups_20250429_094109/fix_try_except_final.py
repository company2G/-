#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
这是app_simple.py文件中嵌套try-except结构问题的最终修复脚本。
修复几个关键问题：
1. 修复"获取详细使用记录"的嵌套try-except结构
2. 修复"获取最近使用记录"的嵌套try-except结构
3. 修正所有缩进问题
4. 修正错误消息内容
"""

import re

def main():
    # 文件路径
    input_file = 'app_simple.py'
    output_file = 'app_simple_fixed_final.py'
    backup_file = 'app_simple.py.bak3'
    
    # 读取原始文件
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 创建备份
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"已创建备份文件: {backup_file}")
    
    # 查找获取客户统计的try-except块的范围
    client_stats_start = -1
    client_stats_try_end = -1
    client_stats_except_start = -1
    client_stats_except_end = -1
    
    for i, line in enumerate(lines):
        if "# 获取新增客户和归属统计" in line:
            client_stats_start = i
        if client_stats_start > 0 and "# 获取详细使用记录" in line:
            client_stats_try_end = i
        if client_stats_try_end > 0 and "except Exception as e:" in line:
            client_stats_except_start = i
            break
    
    # 找到客户统计except块的结束位置
    if client_stats_except_start > 0:
        for i in range(client_stats_except_start + 1, len(lines)):
            if "detailed_usage = []" in lines[i]:
                client_stats_except_end = i
                break
    
    # 确保找到了所有需要的行号
    if -1 in [client_stats_start, client_stats_try_end, client_stats_except_start, client_stats_except_end]:
        print("无法找到所有需要的行号，修复失败")
        return
    
    # 从嵌套except块中移除detailed_usage和recent_usages的初始化
    if client_stats_except_start > 0 and client_stats_except_end > 0:
        lines[client_stats_except_start:client_stats_except_end+1] = [
            lines[client_stats_except_start],  # 保留except行
            "        app.logger.error(f\"获取客户统计出错: {str(e)}\")\n",
            "        new_clients = []\n",
            "        attribution_stats = []\n",
            "        creator_stats = []\n",
            "    \n"
        ]
    
    # 修正"获取详细使用记录"的缩进和try-except结构
    for i in range(client_stats_try_end, len(lines)):
        if "# 获取详细使用记录" in lines[i]:
            lines[i] = "    # 获取详细使用记录\n"
            if "try:" in lines[i+1]:
                lines[i+1] = "    try:\n"
                
                # 找到详细使用记录try块的结束位置
                for j in range(i+2, len(lines)):
                    if lines[j].lstrip().startswith("# 获取最近的使用记录"):
                        # 在获取最近的使用记录之前添加except块
                        lines.insert(j, "    except Exception as e:\n")
                        lines.insert(j+1, "        app.logger.error(f\"获取详细使用记录出错: {str(e)}\")\n")
                        lines.insert(j+2, "        import traceback\n")
                        lines.insert(j+3, "        traceback.print_exc()\n")
                        lines.insert(j+4, "        detailed_usage = []\n")
                        lines.insert(j+5, "    \n")
                        break
    
    # 修正"获取最近的使用记录"的缩进和try-except结构
    for i in range(client_stats_try_end, len(lines)):
        if "# 获取最近的使用记录" in lines[i]:
            lines[i] = "    # 获取最近的使用记录（不分组）\n"
            if i+1 < len(lines) and not lines[i+1].strip().startswith("try:"):
                lines.insert(i+1, "    try:\n")
            else:
                lines[i+1] = "    try:\n"
            
            # 修正查询部分的缩进
            j = i+2
            while j < len(lines) and "recent_usages = [dict_from_row(row)" not in lines[j]:
                if lines[j].startswith("            "):
                    lines[j] = "        " + lines[j][12:]
                j += 1
            
            # 如果找到了recent_usages行，修正它的缩进并添加except块
            if j < len(lines) and "recent_usages = [dict_from_row(row)" in lines[j]:
                lines[j] = "        " + lines[j][12:]
                
                # 添加except块
                lines.insert(j+1, "\n")
                lines.insert(j+2, "    except Exception as e:\n")
                lines.insert(j+3, "        app.logger.error(f\"获取最近使用记录出错: {str(e)}\")\n")
                lines.insert(j+4, "        import traceback\n")
                lines.insert(j+5, "        traceback.print_exc()\n")
                lines.insert(j+6, "        recent_usages = []\n")
                lines.insert(j+7, "    \n")
                break
    
    # 保存修复后的文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"修复已完成并保存到: {output_file}")
    print("请检查修复后的文件是否正确，然后再替换原始文件。")

if __name__ == "__main__":
    main() 