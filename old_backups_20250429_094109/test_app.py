#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试Flask应用是否可以正常启动
"""

import sys
import os
import traceback

print("开始测试Flask应用...")

try:
    # 尝试导入Flask应用
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from app_simple import app
    
    print("成功导入Flask应用！")
    
    # 验证app对象
    print(f"应用名称: {app.name}")
    print(f"路由数量: {len(app.url_map._rules)}")
    
    # 尝试执行app的一些方法
    with app.app_context():
        print("成功创建应用上下文")
    
    print("测试成功完成！应用可以正常启动。")
    
except Exception as e:
    print(f"测试失败: {str(e)}")
    print("详细错误信息:")
    traceback.print_exc()
    
    # 尝试定位错误行
    if hasattr(e, 'lineno') and hasattr(e, 'filename'):
        print(f"错误位置: {e.filename}:{e.lineno}")
    
    # 如果是语法错误，尝试显示相关代码行
    import linecache
    if hasattr(e, 'lineno') and hasattr(e, 'filename'):
        line = linecache.getline(e.filename, e.lineno)
        print(f"错误行内容: {line.strip()}")
        
        # 显示错误行前后的上下文
        print("错误上下文:")
        for i in range(max(1, e.lineno-3), e.lineno+4):
            line = linecache.getline(e.filename, i)
            prefix = ">>>" if i == e.lineno else "   "
            print(f"{prefix} {i}: {line.rstrip()}")
    
    sys.exit(1) 