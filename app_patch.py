"""
禾燃客户管理系统 - 补丁程序
该程序修复admin_required未定义的问题
"""

import sys
import os

def apply_patch():
    """应用补丁：将admin_required装饰器定义注入app_simple.py的开头"""
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_simple.py')
    
    # 读取原文件内容
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经包含admin_required定义
    if 'def admin_required(view):' in content:
        print("补丁已应用，无需重复")
        return
    
    # 找到合适的插入点（在导入部分之后，Flask应用创建之前）
    insertion_point = content.find('app = Flask(__name__)')
    if insertion_point == -1:
        print("错误：找不到合适的插入点")
        return
    
    # 准备要插入的代码
    admin_required_code = '''
# 添加admin_required装饰器
def admin_required(view):
    """检查用户是否为管理员的装饰器"""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        if not g.user.get('role') == 'admin':
            flash('需要管理员权限访问该页面', 'danger')
            return redirect(url_for('dashboard'))
        return view(**kwargs)
    return wrapped_view

'''
    
    # 插入代码
    new_content = content[:insertion_point] + admin_required_code + content[insertion_point:]
    
    # 备份原文件
    backup_path = app_path + '.bak'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 写入修改后的内容
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✓ 补丁已成功应用，原文件已备份为 {backup_path}")

if __name__ == "__main__":
    apply_patch() 