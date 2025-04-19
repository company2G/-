#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
禾燃客户管理系统 - 主应用引导文件
同时支持作为独立应用运行或从app_simple.py主程序调用
"""

from flask import Flask, redirect, url_for
from appointment_manager import appointment_bp, init_app

def create_app():
    """创建应用实例"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev'  # 开发环境密钥
    
    # 注册预约管理蓝图
    app.register_blueprint(appointment_bp)
    
    # 注册数据库清理回调
    init_app(app)
    
    # 根路由重定向到预约管理
    @app.route('/')
    def index():
        return redirect(url_for('appointment.index'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5050)  # 使用不同的端口，避免与主应用冲突 