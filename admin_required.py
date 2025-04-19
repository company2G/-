"""
admin_required装饰器模块
该文件作为独立模块，可以被app_simple.py导入使用
"""
import functools
from flask import g, redirect, url_for, flash

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