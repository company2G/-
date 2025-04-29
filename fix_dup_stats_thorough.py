#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
彻底修复统计数据双倍计算问题
"""

import re
import os

def fix_statistics_double_counting():
    """彻底修复统计数据重复问题"""
    app_path = 'app_simple.py'
    
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找admin_statistics函数开始和结束的位置
    stats_match = re.search(r'@app\.route\(\'/admin/statistics\'\).*?def admin_statistics\(\):.*?return render_template\(.*?\)', content, re.DOTALL)
    
    if not stats_match:
        print("未找到统计函数，无法修复")
        return False
    
    # 提取统计函数的代码
    stats_code = stats_match.group(0)
    
    # 修复方法1: 修复合并代码，确保不会重复计算
    modified_stats = re.sub(
        r'(# 将合并后的结果转为列表并按使用次数排序\s+)(product_usage_stats = list\(product_usage_map\.values\(\)\))',
        r'\1# 清空初始列表，避免双重计算\n        product_usage_stats = []\n        \2',
        stats_code
    )
    
    # 修复方法2: 避免数据重复设置
    modified_stats = re.sub(
        r'(# 更新product_usage变量用于模板\s+)(product_usage = product_usage_stats)',
        r'\1# 确保不重复赋值\n        if not product_usage:\n            \2',
        modified_stats
    )
    
    # 修复方法3: 添加DISTINCT到所有COUNT函数
    modified_stats = re.sub(
        r'COUNT\((\w+\.\w+)\)',
        r'COUNT(DISTINCT \1)',
        modified_stats
    )
    
    # 修复方法4: 修改变量初始化
    modified_stats = re.sub(
        r'(# 准备更多模板可能需要的变量\s+)(product_usage = \[\]\s+operator_usage = \[\]\s+cross_usage = \[\]\s+product_operator = \[\])',
        r'\1# 使用None初始化，避免重复赋值\n    product_usage = None\n    operator_usage = None\n    cross_usage = None\n    product_operator = None',
        modified_stats
    )
    
    # 修复方法5: 修改获取操作人员使用统计的合并逻辑
    modified_stats = re.sub(
        r'(# 将合并后的结果转为列表并按操作次数排序\s+)(operator_stats = list\(operator_stats_map\.values\(\)\))',
        r'\1# 清空初始列表，避免双重计算\n        operator_stats = []\n        \2',
        modified_stats
    )
    
    # 修复方法6: 修改操作人员使用统计的更新逻辑
    modified_stats = re.sub(
        r'(# 更新operator_usage变量用于模板\s+)(operator_usage = \[.*?\])',
        r'\1# 确保不重复赋值\n        if not operator_usage:\n            \2',
        modified_stats,
        flags=re.DOTALL
    )
    
    # 修复方法7: 修改产品与操作人员交叉统计的合并逻辑
    modified_stats = re.sub(
        r'(# 将字典转换为列表\s+)(cross_usage = list\(cross_usage_map\.values\(\)\))',
        r'\1# 清空初始列表，避免双重计算\n        cross_usage = []\n        \2',
        modified_stats
    )
    
    # 修复方法8: 修改按产品分组操作人员使用情况的逻辑
    modified_stats = re.sub(
        r'(# 创建一个产品分组的副本.*?)(product_operator = copy\.deepcopy\(cross_usage\))',
        r'\1# 确保不重复计算\n            product_operator = []\n            \2',
        modified_stats
    )
    
    # 替换原函数代码
    if stats_code != modified_stats:
        modified_content = content.replace(stats_code, modified_stats)
        
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        print(f"已彻底修复{app_path}中的统计数据重复问题")
        return True
    else:
        print(f"未检测到需要修改的内容")
        return False

if __name__ == "__main__":
    print("开始彻底修复统计数据重复问题...")
    
    # 修复统计数据重复
    fix_statistics_double_counting()
    
    print("修复完成！请重启应用以应用更改") 