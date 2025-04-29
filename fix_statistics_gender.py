#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复统计数据重复和客户性别显示问题
"""

import sqlite3
import re
import os

def get_db():
    """获取数据库连接"""
    db = sqlite3.connect('database.db')
    db.row_factory = sqlite3.Row
    return db

def fix_gender_display_in_template():
    """修复性别显示模板问题"""
    template_path = 'templates/admin/statistics.html'
    
    if not os.path.exists(template_path):
        # 检查备选路径
        template_path = 'templates/statistics.html'
        if not os.path.exists(template_path):
            print(f"无法找到统计模板文件")
            return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改性别显示逻辑
    modified_content = re.sub(
        r'<td>{{ \'女\' if client\.gender == \'female\' else \'男\' }}</td>',
        r'<td>{{ client.gender }}</td>',
        content
    )
    
    if content != modified_content:
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print(f"已修复{template_path}中的性别显示逻辑")
        return True
    else:
        print(f"未检测到需要修改的性别显示逻辑")
        return False

def fix_statistics_duplicate():
    """修复app_simple.py中的统计数据重复问题"""
    app_path = 'app_simple.py'
    
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 在admin_statistics函数中添加DISTINCT关键字
    modified_content = re.sub(
        r'(SELECT\s+)([^D].*?\s+FROM\s+product_usage)',
        r'\1DISTINCT \2',
        content
    )
    
    # 2. 对产品与操作人员交叉统计查询添加DISTINCT
    modified_content = re.sub(
        r'(COUNT\()(\w+\.\w+)(\)\s+as\s+usage_count)',
        r'\1DISTINCT \2\3',
        modified_content
    )
    
    if content != modified_content:
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print(f"已修复{app_path}中的统计数据重复问题")
        return True
    else:
        print(f"未检测到需要修改的统计数据重复问题")
        return False

def fix_gender_in_database():
    """修复杨玉环的性别"""
    db = get_db()
    
    try:
        # 查找杨玉环
        client = db.execute("SELECT id, gender FROM client WHERE name = '杨玉环'").fetchone()
        
        if client:
            client_id = client['id']
            gender = client['gender']
            
            # 如果性别是男，修改为女
            if gender == '男':
                db.execute("UPDATE client SET gender = '女' WHERE id = ?", (client_id,))
                db.commit()
                print(f"已将客户'杨玉环'的性别从'男'修改为'女'")
                return True
            else:
                print(f"客户'杨玉环'的性别已经是'{gender}'，无需修改")
        else:
            print("未找到名为'杨玉环'的客户")
    except Exception as e:
        print(f"修复客户性别时出错: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("开始修复问题...")
    
    # 修复性别显示模板
    fix_gender_display_in_template()
    
    # 修复统计数据重复
    fix_statistics_duplicate()
    
    # 修复杨玉环的性别
    fix_gender_in_database()
    
    print("修复完成！") 