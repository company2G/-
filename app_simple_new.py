"""
禾燃客户管理系统 - Flask应用
"""
from flask import Flask, render_template, request, redirect, url_for, flash, session, g, jsonify, abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
import os
import sys
import hashlib
import functools
from datetime import datetime, timedelta
import smtplib
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("警告: 未安装requests库，短信通知功能将不可用。请使用pip install requests安装。")

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import re

# 导入admin_required装饰器
try:
    from auth_helpers import admin_required
except ImportError:
    # 如果导入失败，直接在这里定义装饰器
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

# 创建Flask应用实例
app = Flask(__name__)
app.secret_key = 'dev'
app.config['UPLOAD_FOLDER'] = 'uploads'

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 在这里继续复制原有app_simple.py的其余部分... 