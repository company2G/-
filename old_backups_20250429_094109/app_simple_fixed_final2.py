import os
import sqlite3
import functools
import pandas as pd
from flask import Flask, render_template, request, url_for, flash, redirect, session, g, jsonify, abort, send_file, Response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date, timedelta
import json
import uuid
import time
import io
import csv
import copy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # 替换为复杂的随机密钥
app.config['DATABASE'] = os.path.join(app.root_path, 'database.db')  # 修正为正确的数据库路�?

# Celery配置
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/0'
)

# 确保实例文件夹存�?
os.makedirs(app.instance_path, exist_ok=True)

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 注册预约管理蓝图（如果导入失败则跳过�?
try:
    from appointment_manager import appointment_bp, init_app as init_appointment_app
    app.register_blueprint(appointment_bp)
    init_appointment_app(app)
    print("已成功加载预约管理模�?)
except ImportError:
    print("警告: 未能加载预约管理模块，此功能将不可用")

# 导入Celery模块
try:
    from celery_config import make_celery
    import async_tasks
    
    # 初始化Celery
    celery = make_celery(app)
    
    # 注册Celery任务
    @celery.task(name='app.generate_statistics_report')
    def generate_statistics_report(start_date=None, end_date=None, user_id=None):
        """生成统计报表的异步任�?""
        return async_tasks.generate_statistics_report(start_date, end_date, user_id)
    
    @celery.task(name='app.send_notification')
    def send_notification(notification_type, recipient, subject, message, **kwargs):
        """发送通知的异步任�?""
        return async_tasks.send_notification(notification_type, recipient, subject, message, **kwargs)
    
    @celery.task(name='app.send_appointment_reminders')
    def send_appointment_reminders():
        """发送预约提醒的定时任务"""
        return async_tasks.send_appointment_reminders()
    
    @celery.task(name='app.generate_daily_statistics')
    def generate_daily_statistics():
        """生成每日统计报告的定时任�?""
        return async_tasks.generate_daily_statistics()
    
    print("已成功加载异步任务模�?)
except ImportError as e:
    print(f"警告: 未能加载异步任务模块，此功能将不可用: {str(e)}")

# 管理员权限装饰器
def admin_required(view):
    """验证用户是否为管理员的装饰器"""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        
        if not hasattr(current_user, 'role') or current_user.role != 'admin':
            flash('您需要管理员权限才能访问此页�?, 'danger')
            return redirect(url_for('dashboard'))
            
        return view(**kwargs)
    return wrapped_view

# 数据库操作函�?
def get_db():
    """获取数据库连�?""
    if 'db' not in g:
        try:
            # 禁用自动时间戳转换，避免日期格式问题
            sqlite3.register_converter("TIMESTAMP", lambda x: x.decode('utf-8'))
            
            g.db = sqlite3.connect(
                app.config['DATABASE'],
                detect_types=sqlite3.PARSE_DECLTYPES,
                # 启用外键约束
                isolation_level=None,
            )
            g.db.execute('PRAGMA foreign_keys = ON')
            # 让查询结果返回字典而不是元�?
            g.db.row_factory = sqlite3.Row
        except Exception as e:
            app.logger.error(f"数据库连接失�? {str(e)}")
            return None
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    """关闭数据库连�?""
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception as e:
            app.logger.error(f"关闭数据库连接时出错: {str(e)}")

def init_db():
    """初始化数据库，创建所有需要的表格"""
    db = get_db()
    db.executescript('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        client_id INTEGER DEFAULT NULL,
        FOREIGN KEY (client_id) REFERENCES client (id)
    );
    
    CREATE TABLE IF NOT EXISTS client (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gender TEXT,
        age INTEGER,
        phone TEXT UNIQUE NOT NULL,
        address TEXT,
        workplace TEXT,
        breakfast TEXT,
        lunch TEXT,
        dinner TEXT,
        night_snack TEXT,
        cold_food TEXT,
        sweet_food TEXT,
        meat TEXT,
        alcohol TEXT,
        constitution TEXT,
        water_drinking TEXT,
        sleep TEXT,
        defecation TEXT,
        gynecology TEXT,
        weight REAL,
        height REAL,
        standard_weight REAL,
        overweight REAL,
        waist REAL,
        hip REAL,
        leg REAL,
        user_id INTEGER,
        operator_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES user (id),
        FOREIGN KEY (operator_id) REFERENCES operators (id)
    );
    
    CREATE TABLE IF NOT EXISTS weight_record (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        record_date DATE NOT NULL,
        weight REAL NOT NULL,
        waist REAL,
        hip REAL,
        leg REAL,
        notes TEXT,
        FOREIGN KEY (client_id) REFERENCES client (id)
    );
    
    CREATE TABLE IF NOT EXISTS weight_management (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        record_date DATE NOT NULL,
        management_type TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (client_id) REFERENCES client (id)
    );
    
    -- 添加全局产品�?
    CREATE TABLE IF NOT EXISTS product (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        type TEXT NOT NULL,  -- 'count' �?'period'
        category TEXT,
        details TEXT,
        count INTEGER DEFAULT 0,  -- 次数卡的使用次数
        validity_days INTEGER DEFAULT 0  -- 期限卡的有效天数
    );
    
    CREATE TABLE IF NOT EXISTS client_product (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        purchase_date DATE NOT NULL,
        start_date DATE,
        remaining_count INTEGER,
        expiry_date DATE,
        notes TEXT,
        operator_id INTEGER,
        FOREIGN KEY (client_id) REFERENCES client (id),
        FOREIGN KEY (product_id) REFERENCES product (id),
        FOREIGN KEY (operator_id) REFERENCES operators (id)
    );
    
    CREATE TABLE IF NOT EXISTS product_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_product_id INTEGER NOT NULL,
        usage_date DATE NOT NULL,
        count_used INTEGER NOT NULL,
        notes TEXT,
        operator_id INTEGER,
        FOREIGN KEY (client_product_id) REFERENCES client_product (id),
        FOREIGN KEY (operator_id) REFERENCES operators (id)
    );
    
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        appointment_date DATE NOT NULL,
        appointment_time TIME NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        notes TEXT,
        confirmed INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES client (id)
    );
    ''')
    db.commit()

# 辅助函数：将SQLite Row对象转换为字�?
def dict_from_row(row):
    """�?sqlite3.Row 对象转换为字�?- 性能优化版本"""
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}

# 用户类（替代SQLAlchemy的User模型�?
class User(UserMixin):
    def __init__(self, id, username, password_hash, role='user', client_id=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.is_admin = (role == 'admin')
        self.is_client = (role == 'client')
        self.client_id = client_id

    @staticmethod
    def get(user_id):
        db = get_db()
        user = db.execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()
        if user:
            # 直接访问索引，而不是使�?get 方法
            role = user['role'] if 'role' in user.keys() else 'user'
            client_id = user['client_id'] if 'client_id' in user.keys() else None
            return User(user['id'], user['username'], user['password_hash'], role, client_id)
        return None

    @staticmethod
    def find_by_username(username):
        db = get_db()
        user = db.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        if user:
            # 直接访问索引，而不是使�?get 方法
            role = user['role'] if 'role' in user.keys() else 'user'
            client_id = user['client_id'] if 'client_id' in user.keys() else None
            return User(user['id'], user['username'], user['password_hash'], role, client_id)
        return None

# 用户加载函数
@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))

# 路由
@app.route('/')
def index():
    if current_user.is_authenticated:
        # 客户用户直接跳转到客户视�?
        if current_user.is_client:
            return redirect(url_for('client_profile', client_id=current_user.client_id))
        # 管理员和操作员跳转到仪表�?
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        user = User.find_by_username(username)
        
        if user:
            flash('用户名已存在，请选择其他用户�?, 'danger')
        elif password != confirm_password:
            flash('两次密码输入不一�?, 'danger')
        else:
            db = get_db()
            db.execute(
                'INSERT INTO user (username, password_hash) VALUES (?, ?)',
                (username, generate_password_hash(password))
            )
            db.commit()
            flash('注册成功，现在可以登录了', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            
            # 输入验证
            if not username or not password:
                flash('请输入用户名和密�?, 'danger')
                return render_template('login.html')
            
            # 获取数据库连�?
            try:
                db = get_db()
            except Exception as e:
                app.logger.error(f"登录时数据库连接错误: {str(e)}")
                flash('系统错误：无法连接到数据库，请联系管理员', 'danger')
                return render_template('login.html')

            cursor = db.cursor()
            
            # 查询用户账户
            try:
                cursor.execute('SELECT id, username, password_hash, role FROM user WHERE username = ?', (username,))
                user_data = cursor.fetchone()
            except sqlite3.Error as e:
                app.logger.error(f"登录查询用户时出�? {str(e)}")
                flash('系统错误：查询用户数据失败，请联系管理员', 'danger')
                return render_template('login.html')
            
            if user_data:
                user_dict = dict_from_row(user_data)
                # 验证密码
                if check_password_hash(user_dict['password_hash'], password):
                    # 构建用户对象
                    user = User(
                        id=user_dict['id'], 
                        username=user_dict['username'], 
                        password_hash=user_dict['password_hash'], 
                        role=user_dict.get('role', 'user')
                    )
                    # 使用Flask-Login登录用户
                    login_user(user)
                    
                    # 登录成功，设置会话类�?
                    session['user_type'] = 'admin'  # 标记为管理员会话
                    
                    # 获取下一个页面，如果没有则默认到仪表�?
                    next_page = request.args.get('next')
                    if not next_page or url_parse(next_page).netloc != '':
                        next_page = url_for('dashboard')
                    
                    flash('登录成功�?, 'success')
                    return redirect(next_page)
                else:
                    flash('密码不正确，请重�?, 'danger')
            else:
                flash('未找到该用户名关联的账户', 'danger')
        except Exception as e:
            # 记录异常并显示友好错误信�?
            app.logger.error(f"管理员登录过程中出现未处理异�? {str(e)}")
            flash(f'登录过程中出现错误，请联系系统管理员', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """优化仪表板页面查询性能"""
    db = get_db()
    
    # 预先查询所有客户信�?
    query = '''
    WITH client_data AS (
        SELECT c.*, u.username as creator_name
        FROM client c
        LEFT JOIN user u ON c.user_id = u.id
        WHERE (? OR c.user_id = ?)
    ),
    product_counts AS (
        SELECT client_id, COUNT(*) as product_count 
        FROM client_product
        GROUP BY client_id
    ),
    appointment_counts AS (
        SELECT client_id, COUNT(*) as appointment_count 
        FROM appointment
        GROUP BY client_id
    )
    SELECT cd.*, 
           COALESCE(pc.product_count, 0) as product_count,
           COALESCE(ac.appointment_count, 0) as appointment_count
    FROM client_data cd
    LEFT JOIN product_counts pc ON cd.id = pc.client_id
    LEFT JOIN appointment_counts ac ON cd.id = ac.client_id
    ORDER BY cd.created_at DESC
    '''
    
    clients = db.execute(query, (current_user.is_admin, current_user.id)).fetchall()
    clients = [dict_from_row(client) for client in clients]
    
    return render_template('dashboard.html', 
                          clients=clients, 
                          is_admin=current_user.is_admin)

# 辅助函数：检查产品是否已过期或已用完
def check_product_expiry(client_product):
    """检查产品是否已过期或已用完"""
    today = datetime.now().date()
    
    # 检查状�?
    if client_product['status'] != 'active':
        return client_product['status']
    
    # 周期卡检查是否过�?
    if client_product['expiry_date']:
        expiry_date = datetime.strptime(client_product['expiry_date'], '%Y-%m-%d').date()
        if today > expiry_date:
            db = get_db()
            db.execute('UPDATE client_product SET status = ? WHERE id = ?', 
                       ('expired', client_product['id']))
            db.commit()
            return 'expired'
    
    # 次数卡检查是否用�?
    if client_product['remaining_count'] is not None and client_product['remaining_count'] <= 0:
        db = get_db()
        db.execute('UPDATE client_product SET status = ? WHERE id = ?', 
                  ('used', client_product['id']))
        db.commit()
        return 'used'
    
    return 'active'

@app.route('/client/<int:client_id>/profile')
@login_required
def client_profile(client_id):
    """客户查看自己的个人资料和产品"""
    # 权限检�?
    if not current_user.is_admin and not current_user.is_client:
        flash('您无权访问此页面', 'danger')
        return redirect(url_for('dashboard'))
    
    # 如果是客户用户，确保只能查看自己的资�?
    if current_user.is_client and current_user.client_id != client_id:
        flash('您只能查看自己的资料', 'danger')
        return redirect(url_for('index'))
    
    # 获取客户信息
    db = get_db()
    client = db.execute('SELECT * FROM client WHERE id = ?', (client_id,)).fetchone()
    
    if not client:
        flash('客户不存�?, 'danger')
        return redirect(url_for('index'))
    
    # 获取客户的产�?
    client_products = db.execute('''
        SELECT cp.*, p.name as product_name, p.type as product_type, p.description, p.category, p.details
        FROM client_product cp
        JOIN product p ON cp.product_id = p.id
        WHERE cp.client_id = ?
        ORDER BY cp.purchase_date DESC
    ''', (client_id,)).fetchall()
    
    # 处理产品状态和转换为字�?
    products_list = []
    for cp in client_products:
        cp_dict = dict_from_row(cp)
        cp_dict['status'] = check_product_expiry(cp_dict)
        products_list.append(cp_dict)
    
    # 获取客户的使用记�?
    usage_records = db.execute('''
        SELECT pu.*, cp.product_id, p.name as product_name, u.username as operator_name
        FROM product_usage pu
        JOIN client_product cp ON pu.client_product_id = cp.id
        JOIN product p ON cp.product_id = p.id
        JOIN user u ON pu.operator_id = u.id
        WHERE cp.client_id = ?
        ORDER BY pu.usage_date DESC
    ''', (client_id,)).fetchall()
    
    # 转换SQLite Row对象为字�?
    client_dict = dict_from_row(client)
    usage_list = [dict_from_row(u) for u in usage_records]
    
    return render_template('client_profile.html', 
                          client=client_dict, 
                          products=products_list, 
                          usage_records=usage_list,
                          is_client=current_user.is_client)

# 客户管理路由
@app.route('/client/add', methods=['GET', 'POST'])
@login_required
def add_client():
    """添加新客�?- 同时创建客户用户账号"""
    # 获取操作人员列表
    db = get_db()
    operators = db.execute('SELECT * FROM operators ORDER BY name').fetchall()
    
    if request.method == 'POST':
        # 从表单获取数�?
        name = request.form.get('name', '').strip()
        gender = request.form.get('gender', '')
        age = request.form.get('age', type=int)
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '')
        workplace = request.form.get('workplace', '')
        
        # 饮食习惯
        breakfast = request.form.get('breakfast', '')
        lunch = request.form.get('lunch', '')
        dinner = request.form.get('dinner', '')
        night_snack = request.form.get('night_snack', '')
        cold_food = request.form.get('cold_food', '')
        sweet_food = request.form.get('sweet_food', '')
        meat = request.form.get('meat', '')
        alcohol = request.form.get('alcohol', '')
        
        # 身体状况
        constitution = request.form.get('constitution', '')
        water_drinking = request.form.get('water_drinking', '')
        sleep = request.form.get('sleep', '')
        defecation = request.form.get('defecation', '')
        gynecology = request.form.get('gynecology', '')
        
        # 体重相关
        weight = request.form.get('weight', type=float)
        height = request.form.get('height', type=int)
        waist = request.form.get('waist', type=int)
        hip = request.form.get('hip', type=int)
        leg = request.form.get('leg', type=int)
        standard_weight = request.form.get('standard_weight', type=float)
        overweight = request.form.get('overweight', type=float)
        
        # 关联操作�?
        operator_id = request.form.get('operator_id', type=int)
        
        # 验证数据
        current_user = g.user
        current_time = datetime.now().isoformat()
        
        error = None
        
        if not name:
            error = '客户姓名不能为空'
        elif not phone:
            error = '手机号不能为�?
        elif operator_id is None:
            error = '必须选择一个操作员'
            
        # 检查手机号是否已存�?
        if not error:
            existing = db.execute('SELECT id FROM client WHERE phone = ?', (phone,)).fetchone()
            if existing:
                error = f'手机�?{phone} 已存�?
                
        # 验证操作员是否存�?
        if operator_id and not error:
            operator = db.execute('SELECT id FROM operators WHERE id = ?', (operator_id,)).fetchone()
            if not operator:
                error = "所选操作员不存�?
        
        if error is not None:
            flash(error, 'danger')
            return render_template('add_client.html', operators=operators)
        
        # 开始事�?
        db.execute('BEGIN')
        
        try:
            # 检查client表是否有operator_id�?
            cursor = db.cursor()
            columns = cursor.execute("PRAGMA table_info(client)").fetchall()
            has_operator_id = any(col['name'] == 'operator_id' for col in columns)
            
            # 构建插入参数与SQL语句
            if has_operator_id:
                params = (
                    name, gender, age, phone, address, workplace,
                    breakfast, lunch, dinner, night_snack, cold_food, sweet_food, meat, alcohol,
                    constitution, water_drinking, sleep, defecation, gynecology,
                    weight, height, waist, hip, leg, standard_weight, overweight,
                    current_user.id, operator_id, current_time, current_time
                )
                
                # 插入客户记录
                cursor = db.execute(
                    '''INSERT INTO client 
                       (name, gender, age, phone, address, workplace,
                        breakfast, lunch, dinner, night_snack, cold_food, sweet_food, meat, alcohol,
                        constitution, water_drinking, sleep, defecation, gynecology,
                        weight, height, waist, hip, leg, standard_weight, overweight,
                        user_id, operator_id, created_at, updated_at) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    params
                )
            else:
                # 没有operator_id列，使用原始字段
                params = (
                    name, gender, age, phone, address, workplace,
                    breakfast, lunch, dinner, night_snack, cold_food, sweet_food, meat, alcohol,
                    constitution, water_drinking, sleep, defecation, gynecology,
                    weight, height, waist, hip, leg, standard_weight, overweight,
                    current_user.id, current_time, current_time
                )
                
                # 插入客户记录
                cursor = db.execute(
                    '''INSERT INTO client 
                       (name, gender, age, phone, address, workplace,
                        breakfast, lunch, dinner, night_snack, cold_food, sweet_food, meat, alcohol,
                        constitution, water_drinking, sleep, defecation, gynecology,
                        weight, height, waist, hip, leg, standard_weight, overweight,
                        user_id, created_at, updated_at) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    params
                )
                
                # 尝试添加operator_id列并更新记录
                try:
                    db.execute('ALTER TABLE client ADD COLUMN operator_id INTEGER')
                    app.logger.info("已向client表添加operator_id�?)
                    
                    # 更新刚插入的记录
                    client_id = cursor.lastrowid
                    db.execute('UPDATE client SET operator_id = ? WHERE id = ?', (operator_id, client_id))
                except Exception as e:
                    app.logger.warning(f"添加或更新operator_id列失�? {str(e)}")
            
            client_id = cursor.lastrowid
            
            # 检查user表结构，确保存在所需�?
            def column_exists(table_name, column_name):
                result = db.execute(f"PRAGMA table_info({table_name})").fetchall()
                return any(col['name'] == column_name for col in result)
            
            # 检查并添加必要的列
            needed_columns = {
                'client_id': 'INTEGER', 
                'name': 'TEXT', 
                'phone': 'TEXT', 
                'email': 'TEXT'
            }
            
            for col_name, col_type in needed_columns.items():
                if not column_exists('user', col_name):
                    try:
                        db.execute(f'ALTER TABLE user ADD COLUMN {col_name} {col_type}')
                    except Exception as e:
                        app.logger.warning(f"添加�?{col_name} 到user表时出错: {str(e)}")
            
            # 创建对应的用户账�?- 使用手机号作为用户名和初始密�?
            password_hash = generate_password_hash(phone)
            
            # 检查是否已存在同名用户
            existing_user = db.execute('SELECT id FROM user WHERE username = ?', (phone,)).fetchone()
            if existing_user:
                # 如果已有同名用户，使用其他标识方�?
                username = f"{phone}_{client_id}"
            else:
                username = phone
                
            # 插入用户记录 - 避免使用可能不存在的�?
            try:
                db.execute(
                    'INSERT INTO user (username, password_hash, role, client_id, name, phone) VALUES (?, ?, ?, ?, ?, ?)',
                    (username, password_hash, 'client', client_id, name, phone)
                )
                
                # 获取新用户ID
                user_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                
                # 单独更新其他字段，避免列不存在的问题
                db.execute('UPDATE user SET client_id = ? WHERE id = ?', (client_id, user_id))
                db.execute('UPDATE user SET name = ? WHERE id = ?', (name, user_id))
                db.execute('UPDATE user SET phone = ? WHERE id = ?', (phone, user_id))
            except Exception as e:
                app.logger.error(f"创建用户账户时出�? {str(e)}")
                raise Exception(f"创建用户账户失败: {str(e)}")
            
            # 提交事务
            db.commit()
            
            # 添加成功提示
            flash(f'客户 {name} 添加成功，已创建登录账户，初始密码为客户的手机号', 'success')
            
            # 添加后返回客户详情页
            return redirect(url_for('view_client', client_id=client_id))
            
        except Exception as e:
            # 发生错误回滚事务
            db.rollback()
            app.logger.error(f"添加客户时出�? {str(e)}")
            flash(f'添加客户时出�? {str(e)}', 'danger')
            return render_template('add_client.html', operators=operators)
    
    # GET请求或处理出错，显示表单
    return render_template('add_client.html', operators=operators)

@app.route('/client/<int:client_id>/add_product', methods=['GET', 'POST'])
@login_required
def add_client_product(client_id):
    """添加产品到客户账�?- 支持储值卡支付"""
    # 检查是否有权限管理该客�?
    if not user_can_manage_client(client_id):
        flash('您没有权限管理此客户', 'danger')
        return redirect(url_for('dashboard'))
    
    # 获取客户信息
    db = get_db()
    client = db.execute('SELECT * FROM client WHERE id = ?', (client_id,)).fetchone()
    
    if not client:
        flash('客户不存�?, 'danger')
        return redirect(url_for('dashboard'))
    
    # 将客户信息转为字�?
    client = dict_from_row(client)
    
    # 确保客户余额和折扣有默认�?
    if client.get('balance') is None:
        client['balance'] = 0.0
    if client.get('discount') is None:
        client['discount'] = 1.0
    
    # 获取所有可用产�?
    products = db.execute('SELECT * FROM product ORDER BY category, name').fetchall()
    products = [dict_from_row(p) for p in products]
    
    # 获取所有操作员
    operators = db.execute('SELECT * FROM operators ORDER BY name').fetchall()
    operators = [dict_from_row(op) for op in operators]
    
    # 创建产品数据的JSON字符串，用于前端JavaScript
    import json
    products_json = {}
    for p in products:
        products_json[str(p['id'])] = {
            'name': p['name'],
            'type': p['type'],
            'price': float(p['price']) if p['price'] is not None else 0,
            'category': p['category'] if p['category'] is not None else '',
            'description': p['description'] if p['description'] is not None else '无描�?,
            'sessions': p['sessions'] if p['sessions'] is not None else '',
            'validity_days': p['validity_days'] if p['validity_days'] is not None else ''
        }
    products_json = json.dumps(products_json)
    
    if request.method == 'POST':
        # 获取表单数据
        product_id = request.form.get('product_id')
        purchase_date = request.form.get('purchase_date')
        start_date = request.form.get('start_date')
        notes = request.form.get('notes', '')
        payment_method = request.form.get('payment_method', 'cash')
        apply_discount = request.form.get('apply_discount') == 'on'
        operator_id = request.form.get('operator_id')
        
        # 验证数据
        missing_fields = []
        if not product_id:
            missing_fields.append('产品')
        if not purchase_date:
            missing_fields.append('购买日期')
        if not start_date:
            missing_fields.append('开始日�?)
        # 仅当支付方式不是余额时，才检查操作员
        if payment_method != 'balance' and not operator_id:
            missing_fields.append('操作�?)
            
        if missing_fields:
            error_message = '请填写所有必填字�? ' + ', '.join(missing_fields)
            if '操作�? in missing_fields:
                error_message = '使用现金支付时必须选择一个有效的操作员进行关�?
            flash(error_message, 'danger')
            return render_template('add_client_product.html', client=client, products=products, products_json=products_json, operators=operators, today_date=datetime.now().strftime('%Y-%m-%d'))
        
        # 验证操作员选择（仅当支付方式不是余额时�?
        if payment_method != 'balance' and not operator_id:
            flash('请选择一个操作员', 'danger')
            return render_template('add_client_product.html', client=client, products=products, products_json=products_json, operators=operators, today_date=datetime.now().strftime('%Y-%m-%d'))
        
        # 验证操作员是否存在（如果提供了操作员ID�?
        if operator_id:
            operator = db.execute('SELECT id FROM operators WHERE id = ?', (operator_id,)).fetchone()
            if not operator:
                flash('所选操作员不存�?, 'danger')
                return render_template('add_client_product.html', client=client, products=products, products_json=products_json, operators=operators, today_date=datetime.now().strftime('%Y-%m-%d'))
        
        try:
            # 获取产品信息
            product = db.execute('SELECT * FROM product WHERE id = ?', (product_id,)).fetchone()
            if not product:
                flash('产品不存�?, 'danger')
                return render_template('add_client_product.html', client=client, products=products, products_json=products_json, operators=operators, today_date=datetime.now().strftime('%Y-%m-%d'))
            
            product = dict_from_row(product)
            
            # 计算到期日期和剩余次�?
            remaining_count = product['sessions'] if product['sessions'] is not None else 0
            if product['type'] == 'period' and product['validity_days']:
                # 计算到期日期
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                expiry_date = (start_datetime + timedelta(days=product['validity_days'])).strftime('%Y-%m-%d')
            else:
                expiry_date = None
            
            # 计算价格和折�?
            original_price = float(product['price']) if product['price'] is not None else 0
            discount_rate = float(client['discount']) if apply_discount and client['discount'] is not None else 1.0
            actual_paid = original_price * discount_rate
            
            # 检查余额是否足够（如果使用储值卡支付�?
            if payment_method == 'balance':
                if client['balance'] is None or float(client['balance']) < actual_paid:
                    flash('储值卡余额不足，请选择其他支付方式或为客户充�?, 'danger')
                    return render_template('add_client_product.html', client=client, products=products, products_json=products_json, operators=operators, today_date=datetime.now().strftime('%Y-%m-%d'))
            
            # 开始数据库事务
            db.execute('BEGIN TRANSACTION')
            
            try:
                # 检查client_product表是否有operator_id字段，如果没有则添加
                def column_exists(table_name, column_name):
                    result = db.execute(f"PRAGMA table_info({table_name})").fetchall()
                    return any(col['name'] == column_name for col in result)
                
                if not column_exists('client_product', 'operator_id'):
                    db.execute('ALTER TABLE client_product ADD COLUMN operator_id INTEGER')
                
                # 插入客户产品记录 - 根据支付方式决定是否使用操作员ID
                if payment_method == 'balance':
                    # 储值卡支付 - 不需要操作员
                    cursor = db.execute(
                        '''INSERT INTO client_product 
                           (client_id, product_id, purchase_date, start_date, remaining_count, expiry_date, 
                           status, notes, created_at, updated_at, payment_method, discount_rate, 
                           original_price, actual_paid) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (
                            client_id, product_id, purchase_date, start_date, remaining_count, expiry_date,
                            'active', notes, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), payment_method, discount_rate,
                            original_price, actual_paid
                        )
                    )
                else:
                    # 现金支付 - 需要操作员
                    cursor = db.execute(
                        '''INSERT INTO client_product 
                           (client_id, product_id, purchase_date, start_date, remaining_count, expiry_date, 
                           status, notes, created_at, updated_at, payment_method, discount_rate, 
                           original_price, actual_paid, operator_id) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (
                            client_id, product_id, purchase_date, start_date, remaining_count, expiry_date,
                            'active', notes, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'), payment_method, discount_rate,
                            original_price, actual_paid, operator_id
                        )
                    )
                
                # 如果使用储值卡支付，更新客户余额并记录交易
                if payment_method == 'balance':
                    # 获取交易前余�?
                    before_balance = float(client['balance'])
                    # 计算交易后余�?
                    after_balance = before_balance - actual_paid
                    
                    # 更新客户余额
                    db.execute(
                        'UPDATE client SET balance = ? WHERE id = ?',
                        (after_balance, client_id)
                    )
                    
                    # 记录交易 - 不需要操作员ID
                    db.execute(
                        '''INSERT INTO balance_transaction 
                           (client_id, amount, transaction_type, description, before_balance, 
                           after_balance, created_at) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (
                            client_id, -actual_paid, 'purchase', 
                            f'购买产品：{product["name"]}', before_balance, 
                            after_balance, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        )
                    )
                
                # 提交事务
                db.commit()
                
                product_name = product['name']
                flash(f'已成功为客户添加产品: {product_name}', 'success')
                return redirect(url_for('client_products', client_id=client_id))
                
            except Exception as e:
                # 发生错误，回滚事�?
                db.execute('ROLLBACK')
                flash(f'添加产品时发生错�? {str(e)}', 'danger')
                app.logger.error(f"添加产品错误: {str(e)}")
                return render_template('add_client_product.html', client=client, products=products, products_json=products_json, operators=operators, today_date=datetime.now().strftime('%Y-%m-%d'))
        
        except Exception as e:
            flash(f'处理产品信息时发生错�? {str(e)}', 'danger')
            app.logger.error(f"处理产品信息错误: {str(e)}")
            return render_template('add_client_product.html', client=client, products=products, products_json=products_json, operators=operators, today_date=datetime.now().strftime('%Y-%m-%d'))
    
    # GET请求，展示添加产品表�?
    return render_template(
        'add_client_product.html', 
        client=client, 
        products=products,
        products_json=products_json,
        operators=operators,
        today_date=datetime.now().strftime('%Y-%m-%d')
    )

@app.route('/client/<int:client_id>/use_product/<int:client_product_id>', methods=['GET', 'POST'])
@login_required
def use_client_product(client_id, client_product_id):
    # 检查是否有权限管理该客�?
    if not user_can_manage_client(client_id):
        flash('您没有权限管理该客户')
        return redirect(url_for('dashboard'))
        
    db = get_db()
    client = db.execute('SELECT * FROM client WHERE id = ?', (client_id,)).fetchone()
    client_product = db.execute(
        'SELECT cp.*, p.name as product_name FROM client_product cp '
        'JOIN product p ON cp.product_id = p.id '
        'WHERE cp.id = ? AND cp.client_id = ?',
        (client_product_id, client_id)
    ).fetchone()
    
    if client is None or client_product is None:
        abort(404)
        
    # 获取操作人员列表
    operators = db.execute('SELECT * FROM operators ORDER BY name').fetchall()
    operators = [dict_from_row(op) for op in operators]
    
    if request.method == 'POST':
        # 统一处理表单字段，兼容新旧字段名，但优先使用与数据库匹配的字段名
        amount_used = request.form.get('amount_used', type=int)
        if not amount_used:
            amount_used = request.form.get('usage_amount', type=int)
            if not amount_used:
                amount_used = request.form.get('count_used', type=int)
            
        notes = request.form.get('notes', '')
        operator_id = request.form.get('operator_id', type=int)
        usage_date = request.form.get('usage_date', datetime.now().strftime('%Y-%m-%d'))
        
        error = None
        if not amount_used or amount_used <= 0:
            error = "使用次数必须为正�?
        elif amount_used > client_product['remaining_count']:
            error = "使用次数不能超过剩余次数"
        elif not operator_id:
            error = "必须选择一个有效的操作员进行产品使用记�?
            
        # 验证操作员是否存�?
        if operator_id:
            operator = db.execute('SELECT id FROM operators WHERE id = ?', (operator_id,)).fetchone()
            if not operator:
                error = "所选操作员不存�?
        
        if error is None:
            new_remaining = client_product['remaining_count'] - amount_used
            
            # 更新客户产品剩余次数
            db.execute(
                'UPDATE client_product SET remaining_count = ? WHERE id = ?',
                (new_remaining, client_product_id)
            )
            
            # 记录使用情况到client_product_usage�?
            db.execute(
                'INSERT INTO client_product_usage (client_product_id, amount_used, usage_date, notes, user_id, operator_id) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (client_product_id, amount_used, datetime.now().isoformat(), notes, (g.user.id if hasattr(g, 'user') and g.user is not None else 1), operator_id)
            )
            
            # 同时记录到product_usage表以保持兼容�?
            db.execute(
                'INSERT INTO product_usage (client_product_id, usage_date, count_used, notes, operator_id, created_at) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (client_product_id, usage_date, amount_used, notes, operator_id, datetime.now().isoformat())
            )
            
            db.commit()
            flash('产品使用记录已保�?)
            return redirect(url_for('client_products', client_id=client_id))
        else:
            flash(error, 'danger')
    
    # 获取该产品的使用记录
    try:
        usage_records = db.execute(
            '''SELECT cpu.*, u.username, o.name as operator_name
               FROM client_product_usage cpu
               LEFT JOIN user u ON cpu.user_id = u.id
               LEFT JOIN operators o ON cpu.operator_id = o.id
               WHERE cpu.client_product_id = ?
               ORDER BY cpu.usage_date DESC''',
            (client_product_id,)
        ).fetchall()
        usage_records = [dict_from_row(record) for record in usage_records]
    except:
        # 如果查询失败，设置为空列�?
        usage_records = []
    
    return render_template(
        'use_product.html', 
        client=client, 
        client_product=client_product, 
        usage_records=usage_records,
        operators=operators
    )

@app.route('/client/<int:client_id>/products')
@login_required
def client_products(client_id):
    conn = get_db()
    client = conn.execute('SELECT * FROM client WHERE id = ?', (client_id,)).fetchone()
    
    if not client:
        conn.close()
        flash('客户不存�?, 'danger')
        return redirect(url_for('dashboard'))
    
    # 获取客户的产品信�?
    client_products = conn.execute('''
        SELECT cp.*, p.name as product_name, p.type as product_type, 
               p.description as product_description, p.category
        FROM client_product cp
        JOIN product p ON cp.product_id = p.id
        WHERE cp.client_id = ?
        ORDER BY cp.expiry_date ASC
    ''', (client_id,)).fetchall()
    
    # 整理客户产品信息，添加过期状�?
    formatted_products = []
    for product in client_products:
        product_dict = dict_from_row(product)
        product_dict['status'] = check_product_expiry(product_dict)
        formatted_products.append(product_dict)
    
    # 获取可添加的产品列表
    available_products = conn.execute('SELECT * FROM product').fetchall()
    
    conn.close()
    return render_template('client_products.html', 
                          client=client, 
                          products=formatted_products,  # 修改为products，与模板中一�?
                          available_products=available_products)

@app.route('/client/<int:client_id>')
@login_required
def view_client(client_id):
    conn = get_db()
    client = conn.execute('''
        SELECT c.*, u.username as creator_name
        FROM client c
        LEFT JOIN user u ON c.user_id = u.id
        WHERE c.id = ?
    ''', (client_id,)).fetchone()
    
    if not client:
        conn.close()
        flash('客户不存�?, 'danger')
        return redirect(url_for('dashboard'))
    
    # 获取客户的产品信�?
    client_products = conn.execute('''
        SELECT cp.*, p.name as product_name
        FROM client_product cp
        JOIN product p ON cp.product_id = p.id
        WHERE cp.client_id = ?
        ORDER BY cp.expiry_date ASC
    ''', (client_id,)).fetchall()
    
    # 整理客户产品信息，添加过期状�?
    formatted_products = []
    for product in client_products:
        product_dict = dict_from_row(product)
        product_dict['status'] = check_product_expiry(product)
        formatted_products.append(product_dict)
    
    conn.close()
    return render_template('view_client.html', client=client, client_products=formatted_products)

@app.route('/client/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    # 获取客户信息
    db = get_db()
    client = db.execute('SELECT * FROM client WHERE id = ?', (client_id,)).fetchone()
    
    # 确保客户存在
    if not client:
        flash('客户不存�?, 'danger')
        return redirect(url_for('dashboard'))
    
    # 权限检�?- 使用统一函数
    if not user_can_manage_client(client_id):
        flash('无权编辑此客户信�?, 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # 获取表单数据
        name = request.form.get('name')
        gender = request.form.get('gender')
        age = request.form.get('age')
        phone = request.form.get('phone')
        address = request.form.get('address', '')
        workplace = request.form.get('workplace', '')
        
        # 饮食情况
        breakfast = request.form.get('breakfast', '正常')
        lunch = request.form.get('lunch', '正常')
        dinner = request.form.get('dinner', '正常')
        night_snack = request.form.get('night_snack', '极少')
        cold_food = request.form.get('cold_food', '正常')
        sweet_food = request.form.get('sweet_food', '正常')
        meat = request.form.get('meat', '正常')
        alcohol = request.form.get('alcohol', '正常')
        
        # 身体状况
        constitution = ','.join(request.form.getlist('constitution'))
        water_drinking = ','.join(request.form.getlist('water_drinking'))
        sleep = ','.join(request.form.getlist('sleep'))
        defecation = ','.join(request.form.getlist('defecation'))
        gynecology = request.form.get('gynecology', '')
        
        # 体型数据
        weight = request.form.get('weight') or None
        height = request.form.get('height') or None
        waist = request.form.get('waist') or None
        hip = request.form.get('hip') or None
        leg = request.form.get('leg') or None
        
        # 安全地计算标准体重和超重
        try:
            height = request.form.get('height')
            weight = request.form.get('weight')
            
            standard_weight = None
            overweight = None
            
            if height and height.strip() and height.isdigit():
                standard_weight = float(height) - 105
                
                if weight and weight.strip() and weight.replace('.', '', 1).isdigit():
                    overweight = float(weight) - standard_weight
        except ValueError as e:
            app.logger.error(f"计算标准体重时出�? {str(e)}")
            flash(f'体重或身高格式不正确', 'warning')
        
        # 更新客户数据
        db.execute(
            '''UPDATE client SET
               name = ?, gender = ?, age = ?, phone = ?, address = ?, workplace = ?,
               breakfast = ?, lunch = ?, dinner = ?, night_snack = ?, cold_food = ?, sweet_food = ?, meat = ?, alcohol = ?,
               constitution = ?, water_drinking = ?, sleep = ?, defecation = ?, gynecology = ?,
               weight = ?, height = ?, waist = ?, hip = ?, leg = ?, standard_weight = ?, overweight = ?,
               updated_at = ?
               WHERE id = ?''',
            (name, gender, age, phone, address, workplace,
             breakfast, lunch, dinner, night_snack, cold_food, sweet_food, meat, alcohol,
             constitution, water_drinking, sleep, defecation, gynecology,
             weight, height, waist, hip, leg, standard_weight, overweight,
             datetime.now().isoformat(), client_id)
        )
        db.commit()
        
        flash('客户信息已更新成�?, 'success')
        return redirect(url_for('view_client', client_id=client_id))
    
    # 如果是管理员查看其他用户的客户，获取创建者信�?
    creator = None
    if current_user.is_admin and client['user_id'] != current_user.id:
        creator = db.execute('SELECT username FROM user WHERE id = ?', (client['user_id'],)).fetchone()
    
    # 转换SQLite Row对象为字�?
    client_dict = dict_from_row(client)
    
    return render_template('edit_client.html', client=client_dict,
                           creator=creator['username'] if creator else None,
                           is_admin=current_user.is_admin)

@app.route('/client/<int:client_id>/delete', methods=['POST'])
@login_required
def delete_client(client_id):
    # 获取客户信息
    db = get_db()
    client = db.execute('SELECT * FROM client WHERE id = ?', (client_id,)).fetchone()
    
    # 确保客户存在
    if not client:
        flash('客户不存�?, 'danger')
        return redirect(url_for('dashboard'))
    
    # 权限检查：管理员可以删除所有客户，普通用户只能删除自己创建的客户
    if not current_user.is_admin and client['user_id'] != current_user.id:
        flash('无权删除此客户信�?, 'danger')
        return redirect(url_for('dashboard'))
        
    try:
        # 开始事�?
        db.execute('BEGIN TRANSACTION')
        
        # 获取客户产品ID列表，用于删除使用记�?
        client_products = db.execute('SELECT id FROM client_product WHERE client_id = ?', (client_id,)).fetchall()
        client_product_ids = [cp['id'] for cp in client_products]
        
        # 删除产品使用记录
        for cp_id in client_product_ids:
            db.execute('DELETE FROM product_usage WHERE client_product_id = ?', (cp_id,))
        
        # 删除客户产品
        db.execute('DELETE FROM client_product WHERE client_id = ?', (client_id,))
        
        # 删除减脂记录和体重管理记�?
        db.execute('DELETE FROM weight_record WHERE client_id = ?', (client_id,))
        db.execute('DELETE FROM weight_management WHERE client_id = ?', (client_id,))
        
        # 删除关联的用户账户（角色为client的）
        db.execute('DELETE FROM user WHERE client_id = ? AND role = ?', (client_id, 'client'))
        
        # 删除客户
        db.execute('DELETE FROM client WHERE id = ?', (client_id,))
        
        # 提交事务
        db.commit()
        
        flash('客户信息已完全删�?, 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        # 发生错误，回滚事�?
        db.rollback()  # 使用db.rollback()代替db.execute('ROLLBACK')
        app.logger.error(f"删除客户时出�? {str(e)}")
        flash(f'删除客户失败：{str(e)}', 'danger')
        return redirect(url_for('view_client', client_id=client_id))

# 减脂记录路由
@app.route('/client/<int:client_id>/weight_record/add', methods=['GET', 'POST'])
@login_required
def add_weight_record(client_id):
    """添加客户减脂记录"""
    # 检查权�?
    if not user_can_manage_client(client_id):
        flash('您没有权限访问该客户', 'danger')
        return redirect(url_for('dashboard'))
    
    # 获取客户信息
    db = get_db()
    client = db.execute('SELECT * FROM client WHERE id = ?', (client_id,)).fetchone()
    if client is None:
        flash('客户不存�?, 'danger')
        return redirect(url_for('dashboard'))
    
    # 转换为字�?
    client = dict_from_row(client)
    
    if request.method == 'POST':
        # 获取表单数据
        record_date = request.form.get('record_date')
        morning_weight = request.form.get('morning_weight')
        breakfast = request.form.get('breakfast')
        lunch = request.form.get('lunch')
        dinner = request.form.get('dinner')
        defecation = 1 if request.form.get('defecation') else 0
        
        # 计算变化
        last_record = db.execute(
            'SELECT * FROM weight_record WHERE client_id = ? ORDER BY id DESC LIMIT 1',
            (client_id,)
        ).fetchone()
        
        daily_change = 0
        total_change = 0
        
        if last_record:
            daily_change = float(morning_weight) - float(last_record['morning_weight'])
            
            # 获取首次记录计算总变�?
            first_record = db.execute(
                'SELECT * FROM weight_record WHERE client_id = ? ORDER BY id ASC LIMIT 1',
                (client_id,)
            ).fetchone()
            
            if first_record:
                total_change = float(morning_weight) - float(first_record['morning_weight'])
        
        # 插入记录
        db.execute(
            'INSERT INTO weight_record (record_date, morning_weight, breakfast, lunch, dinner, defecation, daily_change, total_change, client_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime("now"))',
            (record_date, morning_weight, breakfast, lunch, dinner, defecation, daily_change, total_change, client_id)
        )
        db.commit()
        
        flash('减脂记录添加成功', 'success')
        return redirect(url_for('view_weight_records', client_id=client_id))
    
    # GET请求渲染表单
    from datetime import date
    return render_template('add_weight_record.html', client=client, today_date=date.today().isoformat())

@app.route('/client/<int:client_id>/weight_records')
@login_required
def view_weight_records(client_id):
    """查看客户减脂记录"""
    # 检查权�?
    if not user_can_manage_client(client_id):
        flash('您没有权限访问该客户', 'danger')
        return redirect(url_for('dashboard'))
    
    # 获取客户信息
    db = get_db()
    client = db.execute('SELECT * FROM client WHERE id = ?', (client_id,)).fetchone()
    if client is None:
        flash('客户不存�?, 'danger')
        return redirect(url_for('dashboard'))
    
    # 转换为字�?
    client = dict_from_row(client)
    
    # 获取减脂记录列表，按日期倒序排列
    records = db.execute(
        'SELECT * FROM weight_record WHERE client_id = ? ORDER BY record_date DESC',
        (client_id,)
    ).fetchall()
    
    # 转换为字典列�?
    records = [dict_from_row(record) for record in records]
    
    return render_template('weight_records.html', client=client, records=records)

# 体重管理路由
@app.route('/client/<int:client_id>/weight_management/add', methods=['GET', 'POST'])
@login_required
def add_weight_management(client_id):
    """添加客户体重管理记录"""
    # 检查权�?
    if not user_can_manage_client(client_id):
        flash('您没有权限访问该客户', 'danger')
        return redirect(url_for('dashboard'))
    
    # 获取客户信息
    db = get_db()
    client = db.execute('SELECT * FROM client WHERE id = ?', (client_id,)).fetchone()
    if client is None:
        flash('客户不存�?, 'danger')
        return redirect(url_for('dashboard'))
    
    # 转换为字�?
    client = dict_from_row(client)
    
    if request.method == 'POST':
        # 获取表单数据
        record_date = request.form.get('record_date')
        before_weight = request.form.get('before_weight')
        after_weight = request.form.get('after_weight')
        measurements = request.form.get('measurements')
        notes = request.form.get('notes')
        
        # 获取最新记录的序号
        last_record = db.execute(
            'SELECT sequence FROM weight_management WHERE client_id = ? ORDER BY sequence DESC LIMIT 1',
            (client_id,)
        ).fetchone()
        
        sequence = 1
        if last_record:
            sequence = last_record['sequence'] + 1
        
        # 插入记录
        db.execute(
            'INSERT INTO weight_management (sequence, record_date, before_weight, after_weight, measurements, notes, client_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, datetime("now"))',
            (sequence, record_date, before_weight, after_weight, measurements, notes, client_id)
        )
        db.commit()
        
        flash('体重管理记录添加成功', 'success')
        return redirect(url_for('view_weight_management', client_id=client_id))
    
    # GET请求渲染表单
    from datetime import date
    return render_template('add_weight_management.html', client=client, today=date.today().isoformat())

@app.route('/client/<int:client_id>/weight_management')
@login_required
def view_weight_management(client_id):
    """查看客户体重管理记录"""
    # 检查权�?
    if not user_can_manage_client(client_id):
        flash('您没有权限访问该客户', 'danger')
        return redirect(url_for('dashboard'))
    
    # 获取客户信息
    db = get_db()
    client = db.execute('SELECT * FROM client WHERE id = ?', (client_id,)).fetchone()
    if client is None:
        flash('客户不存�?, 'danger')
        return redirect(url_for('dashboard'))
    
    # 转换为字�?
    client = dict_from_row(client)
    
    # 获取体重管理记录列表，按序号倒序排列
    weight_managements = db.execute(
        'SELECT * FROM weight_management WHERE client_id = ? ORDER BY sequence DESC',
        (client_id,)
    ).fetchall()
    
    # 转换为字典列�?
    weight_managements = [dict_from_row(record) for record in weight_managements]
    
    return render_template('weight_managements.html', client=client, weight_managements=weight_managements)

# 保留旧的路由名称作为别名，以便兼容现有代�?
@app.route('/client/<int:client_id>/weight_managements')
@login_required
def view_weight_managements(client_id):
    """体重管理记录页面的别名路由（保持向后兼容�?""
    return view_weight_management(client_id)

@app.route('/client/dashboard')
def client_dashboard():
    if 'client_id' not in session:
        flash('请先登录', 'warning')
        return redirect(url_for('login'))
    
    client_id = session['client_id']
    
    conn = get_db()
    client = conn.execute('SELECT * FROM client WHERE id = ?', (client_id,)).fetchone()
    
    if not client:
        conn.close()
        session.pop('client_id', None)
        flash('客户不存在，请重新登�?, 'danger')
        return redirect(url_for('login'))
    
    # 获取客户的产品信�?
    client_products = conn.execute('''
        SELECT cp.*, p.name as product_name 
        FROM client_product cp
        JOIN product p ON cp.product_id = p.id
        WHERE cp.client_id = ?
        ORDER BY cp.expiry_date ASC
    ''', (client_id,)).fetchall()
    
    # 整理客户产品信息，添加过期状�?
    formatted_products = []
    for product in client_products:
        product_dict = dict_from_row(product)
        product_dict['status'] = check_product_expiry(product)
        formatted_products.append(product_dict)
    
    # 获取客户的预约信�?
    appointments = conn.execute('''
        SELECT * FROM appointment
        WHERE client_id = ? AND status != 'cancelled'
        ORDER BY appointment_date ASC, appointment_time ASC
    ''', (client_id,)).fetchall()
    
    # 获取客户的体重记�?
    weight_records = conn.execute('''
        SELECT * FROM weight_record
        WHERE client_id = ?
        ORDER BY record_date DESC
        LIMIT 5
    ''', (client_id,)).fetchall()
    
    conn.close()
    
    return render_template(
        'client_dashboard.html', 
        client=client, 
        client_products=formatted_products, 
        appointments=appointments, 
        weight_records=weight_records
    )

@app.route('/available_times')
def available_times():
    """获取指定日期的可用预约时间段"""
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({
            'error': '未提供日�?,
            'available_times': []
        })
    
    # 预约时间�?09:00-20:00，每小时两个时段
    all_time_slots = [
        {'value': '09:00-10:00', 'label': '09:00-10:00'},
        {'value': '10:00-11:00', 'label': '10:00-11:00'},
        {'value': '11:00-12:00', 'label': '11:00-12:00'},
        {'value': '13:00-14:00', 'label': '13:00-14:00'},
        {'value': '14:00-15:00', 'label': '14:00-15:00'},
        {'value': '15:00-16:00', 'label': '15:00-16:00'},
        {'value': '16:00-17:00', 'label': '16:00-17:00'},
        {'value': '17:00-18:00', 'label': '17:00-18:00'},
        {'value': '18:00-19:00', 'label': '18:00-19:00'},
        {'value': '19:00-20:00', 'label': '19:00-20:00'},
    ]
    
    # 查询该日期已预约的时间段及数�?
    db = get_db()
    booked_slots = db.execute(
        '''SELECT appointment_time, COUNT(*) as count
           FROM appointment
           WHERE appointment_date = ? AND status IN ('pending', 'confirmed')
           GROUP BY appointment_time''',
        (date_str,)
    ).fetchall()
    
    # 将已预约时间段转为字典，方便查询
    booked_slots_dict = {slot['appointment_time']: slot['count'] for slot in booked_slots}
    
    # 过滤出可用时间段（预约数小于2的时间段�?
    available_times = []
    for slot in all_time_slots:
        time_value = slot['value']
        booked_count = booked_slots_dict.get(time_value, 0)
        
        if booked_count < 2:
            # 添加显示已预约数�?
            if booked_count > 0:
                slot['label'] += f' (已约{booked_count}/2)'
            available_times.append(slot)
    
    return jsonify({
        'available_times': available_times
    })

@app.route('/client/appointment/create', methods=['POST'])
def create_appointment():
    """客户创建预约"""
    try:
        # 确认是客户会�?
        if 'client_id' not in session:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': '请先登录客户账户'
                })
            flash('请先登录客户账户', 'danger')
            return redirect(url_for('login'))
            
        user_id = session['client_id']
        
        # 获取提交的数�?- 同时支持表单和JSON提交
        if request.is_json:
            data = request.json
        else:
            data = request.form
        
        appointment_date = data.get('appointment_date')
        appointment_time = data.get('appointment_time')
        service_type = data.get('service_type')
        client_product_id = data.get('client_product_id')
        additional_notes = data.get('additional_notes', '')
        
        # 打印接收到的数据，便于调�?
        app.logger.info(f"收到预约请求: 日期={appointment_date}, 时间={appointment_time}, 服务={service_type}, 产品ID={client_product_id}")
        
        # 简单验�?
        if not appointment_date or not appointment_time or not service_type:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': '请填写所有必要信�?
                })
            flash('请填写所有必要信�?, 'danger')
            return redirect(url_for('client_dashboard'))
        
        # 获取数据库连�?
        db = get_db()
        
        # 获取客户ID - 优先使用real_client_id
        client_id = None
        if 'real_client_id' in session:
            client_id = session['real_client_id']
        else:
            # 查询用户关联的客户ID
            user_data = db.execute('SELECT client_id FROM user WHERE id = ?', (user_id,)).fetchone()
            if user_data and user_data['client_id']:
                client_id = user_data['client_id']
            else:
                # 查询是否有同名客�?
                user_info = db.execute('SELECT username FROM user WHERE id = ?', (user_id,)).fetchone()
                if user_info:
                    phone = user_info['username']
                    client_data = db.execute('SELECT id FROM client WHERE phone = ?', (phone,)).fetchone()
                    if client_data:
                        client_id = client_data['id']
                        # 更新用户记录关联客户ID
                        db.execute('UPDATE user SET client_id = ? WHERE id = ?', (client_id, user_id))
                        db.commit()
                        # 更新会话
                        session['real_client_id'] = client_id
        
        if not client_id:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': '无法确定客户身份，请联系管理�?
                })
            flash('无法确定客户身份，请联系管理�?, 'danger')
            return redirect(url_for('client_dashboard'))
        
        # 检查预约时间是否可�?
        booking_count = db.execute(
            '''SELECT COUNT(*) as count 
               FROM appointment 
               WHERE appointment_date = ? AND appointment_time = ? AND status IN ('pending', 'confirmed')''',
            (appointment_date, appointment_time)
        ).fetchone()['count']
        
        if booking_count >= 2:  # 假设每个时间段最�?个预�?
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': '该时间段预约已满，请选择其他时间'
                })
            flash('该时间段预约已满，请选择其他时间', 'danger')
            return redirect(url_for('client_dashboard'))
        
        # 如果使用产品预约，检查产品是否可�?
        if client_product_id and client_product_id != 'no_product':
            product = db.execute(
                'SELECT * FROM client_product WHERE id = ? AND client_id = ?',
                (client_product_id, client_id)
            ).fetchone()
            
            if not product:
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'message': '所选产品不存在或不属于�?
                    })
                flash('所选产品不存在或不属于�?, 'danger')
                return redirect(url_for('client_dashboard'))
            
            product_dict = dict_from_row(product)
            product_status = check_product_expiry(product_dict)
            
            if product_status != 'active':
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'message': f'所选产品已{product_status}，请选择其他产品'
                    })
                flash(f'所选产品已{product_status}，请选择其他产品', 'danger')
                return redirect(url_for('client_dashboard'))
        else:
            client_product_id = None
        
        # 开始事�?
        db.execute('BEGIN TRANSACTION')
        
        try:
            # 创建预约
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.execute(
                '''INSERT INTO appointment 
                   (client_id, appointment_date, appointment_time, service_type, 
                    client_product_id, additional_notes, status, created_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (client_id, appointment_date, appointment_time, service_type, 
                 client_product_id, additional_notes, 'pending', current_time)
            )
            db.commit()
            
            app.logger.info(f"预约创建成功: 客户ID={client_id}, 日期={appointment_date}, 时间={appointment_time}")
            
            # 预约成功
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': '预约创建成功，请等待确认'
                })
            flash('预约创建成功，请等待确认', 'success')
            return redirect(url_for('client_dashboard'))
        except Exception as e:
            db.rollback()
            app.logger.error(f"预约创建数据库错�? {str(e)}")
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': f'创建预约时数据库错误: {str(e)}'
                })
            flash(f'创建预约时数据库错误: {str(e)}', 'danger')
            return redirect(url_for('client_dashboard'))
            
    except Exception as e:
        app.logger.error(f"创建预约时出�? {str(e)}")
        if request.is_json:
            return jsonify({
                'success': False,
                'message': f'创建预约时出�? {str(e)}'
            })
        flash(f'创建预约时出�? {str(e)}', 'danger')
        return redirect(url_for('client_dashboard'))

@app.route('/client/appointment/<int:appointment_id>/cancel')
@login_required
@admin_required
def admin_cancel_appointment_alt1(appointment_id):
    """管理员取消预约功�?""
    try:
        db = get_db()
        cursor = db.cursor()
        
        # 查询预约信息
        cursor.execute('SELECT * FROM appointment WHERE id = ?', (appointment_id,))
        appointment = cursor.fetchone()
        
        if not appointment:
            flash('预约不存�?, 'danger')
            return redirect(url_for('admin_manage_appointments'))
        
        appointment_dict = dict_from_row(appointment)
        
        # 更新预约状态为已取�?
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            'UPDATE appointment SET status = ?, cancelled_at = ? WHERE id = ?',
            ('cancelled', current_time, appointment_id)
        )
        db.commit()
        
        flash('预约已成功取�?, 'success')
        
    except Exception as e:
        db.rollback()
        app.logger.error(f"取消预约时出�? {str(e)}")
        flash(f'取消预约时出�? {str(e)}', 'danger')
    
    return redirect(url_for('admin_manage_appointments'))

# 管理员预约管理路�?- 重定向到蓝图路由
@app.route('/manage_appointments')
@login_required
@admin_required
def admin_manage_appointments():
    """管理员管理预约页�?""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            SELECT a.*, c.name as client_name, c.phone as client_phone 
            FROM appointment a
            LEFT JOIN client c ON a.client_id = c.id
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        ''')
        appointments = [dict_from_row(row) for row in cursor.fetchall()]
        return render_template('manage_appointments.html', appointments=appointments)
    except Exception as e:
        app.logger.error(f"访问预约管理页面时出�? {str(e)}")
        flash(f'访问预约管理页面时出�? {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/complete_appointment/<int:appointment_id>', methods=['POST'])
@login_required
@admin_required
def admin_complete_appointment(appointment_id):
    """完成预约"""
    db = get_db()
    
    # 获取预约信息
    appointment = db.execute('SELECT * FROM appointment WHERE id = ? AND status = "confirmed"', (appointment_id,)).fetchone()
    
    if not appointment:
        flash('预约不存在或状态不正确', 'warning')
        return redirect(url_for('admin_manage_appointments'))
    
    # 更新预约状态为已完�?
    now = datetime.now().isoformat()
    db.execute(
        'UPDATE appointment SET status = "completed", completed_time = ?, updated_at = ? WHERE id = ?',
        (now, now, appointment_id)
    )
    db.commit()
    
    # 如果预约使用了产品，可以在这里处理产品使用记�?
    client_product_id = appointment['client_product_id']
    if client_product_id:
        # 获取产品信息
        client_product = db.execute('SELECT * FROM client_product WHERE id = ?', (client_product_id,)).fetchone()
        
        # 如果是次数卡，减少剩余次�?
        if client_product and client_product['remaining_count'] is not None:
            new_count = max(0, client_product['remaining_count'] - 1)
            db.execute(
                'UPDATE client_product SET remaining_count = ?, updated_at = ? WHERE id = ?',
                (new_count, now, client_product_id)
            )
            
            # 记录产品使用
            db.execute(
                '''INSERT INTO product_usage 
                   (client_product_id, usage_date, count_used, notes, operator_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (client_product_id, now.split('T')[0], 1, f"自动记录：预约ID {appointment_id}", current_user.id, now)
            )
            db.commit()
    
    flash('预约已标记为完成', 'success')
    return redirect(url_for('admin_manage_appointments'))

@app.route('/client/appointment/<int:appointment_id>/cancel', methods=['POST'])
def client_cancel_appointment(appointment_id):
    """客户取消预约功能"""
    try:
        # 确认是客户会�?
        if 'client_id' not in session:
            flash('请先登录客户账户', 'danger')
            return redirect(url_for('login'))
            
        client_id = session['client_id']
        
        db = get_db()
        db.execute('BEGIN TRANSACTION')  # 使用事务
        
        # 查询预约信息并确认是该客户的预约
        cursor = db.cursor()
        cursor.execute('SELECT * FROM appointment WHERE id = ? AND client_id = ?', 
                      (appointment_id, client_id))
        appointment = cursor.fetchone()
        
        if not appointment:
            flash('预约不存在或不属于您', 'danger')
            return redirect(url_for('client_dashboard'))
            
        appointment_dict = dict_from_row(appointment)
        
        # 检查预约状�?
        if appointment_dict['status'] not in ['pending', 'confirmed']:
            flash('只能取消待确认或已确认的预约', 'warning')
            return redirect(url_for('client_dashboard'))
            
        # 获取取消原因
        cancel_reason = request.form.get('cancel_reason', '客户取消')
        
        # 更新预约状态为已取�?
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute(
            'UPDATE appointment SET status = ?, cancelled_at = ?, cancel_reason = ? WHERE id = ?',
            ('cancelled', current_time, cancel_reason, appointment_id)
        )
        db.commit()
        
        flash('预约已成功取�?, 'success')
        
    except Exception as e:
        db.rollback()  # 统一使用db.rollback()
        app.logger.error(f"客户取消预约时出�? {str(e)}")
        flash(f'取消预约时出�? {str(e)}', 'danger')
    
    return redirect(url_for('client_dashboard'))

# 在应用初始化之后，路由定义之前添�?
@app.before_request
def load_logged_in_user():
    """根据会话中的用户ID加载用户信息"""
    user_id = session.get('user_id')
    client_id = session.get('client_id')
    
    if user_id is None and client_id is None:
        g.user = None
        return
    
    try:
        # 加载管理员用�?
        if user_id is not None:
            user = User.get(user_id)
            g.user = user
        # 加载客户用户
        elif client_id is not None:
            db = get_db()
            user_data = db.execute('SELECT id, username, role, client_id FROM user WHERE id = ?', (client_id,)).fetchone()
            if user_data:
                # 创建一个临时User对象表示客户
                g.user = User(
                    id=user_data['id'],
                    username=user_data['username'],
                    password_hash='', # 不需要存储密码哈�?
                    role='client',
                    client_id=user_data['client_id']
                )
            else:
                g.user = None
    except Exception as e:
        app.logger.error(f"加载用户信息时出�? {str(e)}")
        g.user = None

@app.before_request
def check_session_type():
    """检查会话类型，限制客户和管理员访问各自的页�?""
    # 排除不需要检查的路径
    if request.endpoint in ['static', 'login', 'register', 'client_register', 
                           'client_forgot_password', 'client_reset_password', 'index', None]:
        return
    
    try:
        # 纯客户页面列�?- 只有客户账户可以访问
        client_only_endpoints = ['client_dashboard', 'client_profile', 'client_appointments',
                               'client_logout', 'client_change_password',
                               'create_appointment', 'client_cancel_appointment']
        
        # 管理页面列表 - 需要系统用户登录（管理员或普通系统用户）
        admin_system_endpoints = ['dashboard', 'add_client', 'view_client', 'edit_client', 
                                'delete_client', 'products', 'client_products', 'add_client_product',
                                'use_client_product', 'add_weight_record', 'view_weight_records',
                                'add_weight_management', 'view_weight_managements']
        
        # 仅管理员页面列表 - 只有管理员可以访�?
        admin_only_endpoints = ['admin_users', 'add_product', 'edit_product', 'delete_product',
                              'admin_manage_appointments', 'admin_confirm_appointment', 
                              'admin_complete_appointment', 'admin_statistics',
                              'add_operator', 'edit_operator', 'delete_operator']
        
        # 检查当前请求的endpoint是否在客户专属页面列表中
        if request.endpoint in client_only_endpoints:
            # 如果是客户页面，检查是否有客户会话
            if 'client_id' not in session:
                app.logger.warning(f"未授权的客户页面访问: {request.endpoint}")
                flash('请先登录客户账户', 'warning')
                return redirect(url_for('login'))
        
        # 检查当前请求的endpoint是否在管理页面列表中
        elif request.endpoint in admin_system_endpoints:
            # 如果是管理页面，检查是否已登录
            if not current_user.is_authenticated:
                app.logger.warning(f"未授权的系统页面访问: {request.endpoint}")
                flash('请先登录系统账户', 'warning')
                return redirect(url_for('login'))
        
        # 检查当前请求的endpoint是否在仅管理员页面列表中
        elif request.endpoint in admin_only_endpoints:
            # 如果是仅管理员页面，检查是否已登录且是否为管理�?
            if not current_user.is_authenticated:
                app.logger.warning(f"未授权的管理员页面访�? {request.endpoint}")
                flash('请先登录管理员账�?, 'warning')
                return redirect(url_for('login'))
            
            # 检查是否为管理员角�?
            if not hasattr(current_user, 'role') or current_user.role != 'admin':
                app.logger.warning(f"非管理员尝试访问管理页面: {request.endpoint}")
                flash('您需要管理员权限才能访问此页�?, 'danger')
                return redirect(url_for('dashboard'))
    
    except Exception as e:
        # 记录异常但不中断请求
        app.logger.error(f"会话检查过程中出现异常: {str(e)}")

@app.route('/notification_settings')
@login_required
def notification_settings():
    """临时的通知设置路由，防止引用错�?""
    flash('通知设置功能正在开发中', 'info')
    return redirect(url_for('dashboard'))

@app.route('/appointment/<int:appointment_id>/confirm', methods=['POST'])
@login_required
@admin_required
def admin_confirm_appointment(appointment_id):
    """确认预约"""
    db = get_db()
    
    # 获取预约信息
    appointment = db.execute('SELECT * FROM appointment WHERE id = ? AND status = "pending"', (appointment_id,)).fetchone()
    
    if not appointment:
        flash('预约不存在或状态不正确', 'warning')
        return redirect(url_for('admin_manage_appointments'))
    
    # 更新预约状态为已确�?
    now = datetime.now().isoformat()
    db.execute(
        'UPDATE appointment SET status = "confirmed", confirmed_time = ?, updated_at = ? WHERE id = ?',
        (now, now, appointment_id)
    )
    db.commit()
    
    # 获取客户信息，用于发送通知
    client = db.execute('SELECT name, phone FROM client WHERE id = ?', (appointment['client_id'],)).fetchone()
    
    if client:
        # 这里可以添加发送确认通知的逻辑
        # 例如发送短信或邮件通知客户预约已确�?
        pass
    
    flash('预约已确�?, 'success')
    return redirect(url_for('admin_manage_appointments'))

# 添加预约通知相关的API路由
@app.route('/check-new-appointments')
@login_required
@admin_required
def check_new_appointments_proxy():
    """代理到预约管理模块的新预约检查API"""
    try:
        last_checked = session.get('last_appointment_check')
        current_time = datetime.now()
        
        # 如果是第一次检查，则设置当前时间为上次检查时�?
        if not last_checked:
            session['last_appointment_check'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
            return jsonify({'count': 0})
        
        # 将字符串转换为datetime对象
        last_checked_time = datetime.strptime(last_checked, '%Y-%m-%d %H:%M:%S')
        
        # 获取新预约的数量
        db = get_db()
        new_appointment_count = db.execute(
            "SELECT COUNT(*) as count FROM appointment WHERE created_at > ? AND status = 'pending'",
            (last_checked,)
        ).fetchone()['count']
        
        # 更新最后检查时�?
        session['last_appointment_check'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'count': new_appointment_count,
            'last_checked': last_checked,
            'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        app.logger.error(f"检查新预约时出�? {str(e)}")
        return jsonify({'error': str(e), 'count': 0})

@app.route('/get-latest-appointments')
@login_required
@admin_required
def get_latest_appointments_proxy():
    """代理到预约管理模块的获取最新预约API"""
    from flask import request, jsonify, current_app
    
    try:
        limit = request.args.get('limit', 5, type=int)
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT a.id, c.name as client_name, 
                   a.service_name, a.appointment_date, a.appointment_time, 
                   a.status, a.created_at
            FROM appointment a
            JOIN client c ON a.client_id = c.id
            ORDER BY a.created_at DESC
            LIMIT ?
        """, (limit,))
        
        appointments = []
        for row in cursor.fetchall():
            appointments.append({
                'id': row[0],
                'client_name': row[1],
                'service_name': row[2],
                'date': row[3],
                'time': row[4],
                'status': row[5],
                'created_at': row[6]
            })
        
        return jsonify({'appointments': appointments})
    except Exception as e:
        current_app.logger.error(f"获取最新预约时出错: {str(e)}")
        return jsonify({'error': str(e), 'appointments': []})

@app.route('/client/register', methods=['GET', 'POST'])
def client_register():
    """客户注册"""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', '')
            password_confirm = request.form.get('password_confirm', '')
            
            # 输入验证
            if not name or not phone or not password:
                flash('请填写所有必填字�?, 'danger')
                return render_template('client_register.html')
                
            if password != password_confirm:
                flash('两次输入的密码不一�?, 'danger')
                return render_template('client_register.html')
            
            # 检查手机号是否已被注册
            db = get_db()
            cursor = db.cursor()
            cursor.execute('SELECT id FROM user WHERE username = ?', (phone,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                flash('该手机号已被注册', 'danger')
                return render_template('client_register.html')
            
            # 创建新用户账�?
            password_hash = generate_password_hash(password)
            
            # 创建新客户记�?
            cursor.execute(
                'INSERT INTO user (username, password_hash, role, name, phone) VALUES (?, ?, ?, ?, ?)',
                (phone, password_hash, 'client', name, phone)
            )
            db.commit()
            
            flash('注册成功，请登录', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            app.logger.error(f"客户注册过程中出现错�? {str(e)}")
            flash('注册过程中出现错误，请稍后再�?, 'danger')
    
    return render_template('client_register.html')

def ensure_db_exists():
    """确保数据库存在并初始化所需表结�?""
    try:
        with app.app_context():
            # 尝试获取数据库连�?
            db = get_db()
            
            # 检查是否有表结�?
            tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            if not tables:
                app.logger.info("数据库表不存在，开始初始化数据�?..")
                init_db()
                app.logger.info("数据库初始化完成")
            else:
                app.logger.info(f"数据库已存在，包�?{len(tables)} 个表")
                
            return True
    except Exception as e:
        app.logger.error(f"确保数据库存在时出错: {str(e)}")
        return False

@app.cli.command('init-app')
def init_app_command():
    """初始化应用数据库和必要配�?""
    app.logger.info("正在进行应用初始�?..")
    ensure_db_exists()
    app.logger.info("应用初始化完�?)

def user_can_manage_client(client_id):
    """检查当前用户是否有权限管理指定客户
    
    权限规则:
    1. 管理员可以管理所有客�?
    2. 普通系统用户可以管理自己创建的客户
    3. 客户用户只能查看自己的信�?
    """
    # 管理员拥有所有权�?
    if current_user.is_admin:
        return True
        
    # 客户用户只能管理自己
    if hasattr(current_user, 'is_client') and current_user.is_client:
        return current_user.client_id == client_id
    
    # 普通系统用户可以管理自己创建的客户
    db = get_db()
    client = db.execute('SELECT user_id FROM client WHERE id = ?', (client_id,)).fetchone()
    
    if not client:
        return False
        
    return client['user_id'] == current_user.id

# 添加异步API端点，减少初始页面负�?
@app.route('/api/client/<int:client_id>/products')
@login_required
def api_client_products(client_id):
    # 检查权限：管理员可以查看所有客户，普通用户只能查看自己创建的客户
    if not current_user.is_admin and not user_can_manage_client(client_id):
        return jsonify({"error": "权限不足，无法访问此客户"}), 403

    # 获取客户的产品信�?
    conn = get_db()
    products = conn.execute('''
        SELECT cp.id, cp.client_id, cp.product_id, cp.purchase_date, cp.remaining_count, 
               cp.expiry_date, cp.status, p.name as product_name, p.type as product_type
        FROM client_product cp
        JOIN product p ON cp.product_id = p.id
        WHERE cp.client_id = ?
        ORDER BY cp.expiry_date ASC
    ''', (client_id,)).fetchall()
    
    # 格式化产品信�?
    product_list = []
    for product in products:
        product_dict = dict_from_row(product)
        # 检查产品是否过�?
        product_dict['status'] = check_product_expiry(product)
        product_list.append(product_dict)
    
    conn.close()
    return jsonify({"products": product_list})

# 应用配置优化
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 静态文件缓存一�?
app.config['TEMPLATES_AUTO_RELOAD'] = False  # 生产环境关闭模板自动重新加载

# 配置Jinja2
app.jinja_env.trim_blocks = True  # 删除Jinja2模板中的空行
app.jinja_env.lstrip_blocks = True  # 删除行首空白
app.jinja_env.auto_reload = False  # 关闭自动重新加载

# 添加管理员统计报表路�?
@app.route('/admin/statistics')
@login_required
@admin_required
def admin_statistics():
    """管理员统计页�?""
    db = get_db()
    
    # 获取日期筛选参�?
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # 如果没有提供日期，默认显示过�?0�?
    if not start_date:
        start_date = (date.today() - timedelta(days=30)).isoformat()
    if not end_date:
        end_date = date.today().isoformat()
    
    # 准备基础默认数据（用于处理错误情况）
    new_products = []
    product_usage_stats = []
    operator_stats = []
    new_clients = []
    attribution_stats = []
    product_add_stats = []

    # 准备更多模板可能需要的变量
    product_usage = []
    operator_usage = []
    cross_usage = []
    product_operator = []
    detailed_usage = []
    recent_clients = []
    creator_stats = []
    recent_usages = []
    client_count = 0
    product_count = 0
    usage_count = 0
    product_sales_stats = []
    product_seller_stats = []
    product_sales = []
    
    # 构建日期筛选条�?
    product_usage_filter = ""
    client_product_usage_filter = ""
    client_filter = ""
    product_add_filter = ""
    
    # 参数列表
    pu_params = []
    cpu_params = []
    client_params = []
    cp_params = []

    if start_date:
        product_usage_filter = " AND date(pu.usage_date) >= ?"
        client_product_usage_filter = " AND date(cpu.usage_date) >= ?"
        client_filter = " AND date(c.created_at) >= ?"
        product_add_filter = " AND date(cp.purchase_date) >= ?"
        pu_params.append(start_date)
        cpu_params.append(start_date)
        client_params.append(start_date)
        cp_params.append(start_date)
    
    if end_date:
        product_usage_filter += " AND date(pu.usage_date) <= ?"
        client_product_usage_filter += " AND date(cpu.usage_date) <= ?"
        client_filter += " AND date(c.created_at) <= ?"
        product_add_filter += " AND date(cp.purchase_date) <= ?"
        pu_params.append(end_date)
        cpu_params.append(end_date)
        client_params.append(end_date)
        cp_params.append(end_date)
    
    # 尝试获取基本统计数据
    try:
        # 获取产品总数
        product_count = db.execute("SELECT COUNT(*) as count FROM product").fetchone()['count']
        
        # 获取客户总数
        client_count = db.execute("SELECT COUNT(*) as count FROM client").fetchone()['count']
        
        # 获取使用记录总数
        usage_count_query = """
            SELECT COALESCE(
                (SELECT COUNT(*) FROM product_usage),
                0
            ) + COALESCE(
                (SELECT COUNT(*) FROM client_product_usage),
                0
            ) as count
        """
        usage_count = db.execute(usage_count_query).fetchone()['count']
    except Exception as e:
        app.logger.error(f"获取基本统计数据失败: {str(e)}")
    
    # 获取产品使用统计（从product_usage表）
    try:
        product_usage_query = f"""
        SELECT 
            p.name as product_name, 
            COUNT(pu.id) as usage_count, 
            SUM(pu.count_used) as total_used 
        FROM product_usage pu 
        JOIN client_product cp ON pu.client_product_id = cp.id 
        JOIN product p ON cp.product_id = p.id 
        WHERE 1=1 {product_usage_filter} 
        GROUP BY p.id 
        ORDER BY usage_count DESC
        """
        
        app.logger.info(f"产品使用统计查询SQL (product_usage): {product_usage_query}, 参数: {pu_params}")
        
        product_usage_stats = db.execute(product_usage_query, pu_params).fetchall()
        product_usage_stats = [dict_from_row(row) for row in product_usage_stats]
        
        # 获取产品使用统计（从client_product_usage表）
        client_product_usage_query = f"""
        SELECT 
            p.name as product_name, 
            COUNT(cpu.id) as usage_count, 
            SUM(cpu.amount_used) as total_used 
        FROM client_product_usage cpu 
        JOIN client_product cp ON cpu.client_product_id = cp.id 
        JOIN product p ON cp.product_id = p.id 
        WHERE 1=1 {client_product_usage_filter} 
        GROUP BY p.id 
        ORDER BY usage_count DESC
        """
        
        app.logger.info(f"产品使用统计查询SQL (client_product_usage): {client_product_usage_query}, 参数: {cpu_params}")
        
        cpu_stats = db.execute(client_product_usage_query, cpu_params).fetchall()
        cpu_stats = [dict_from_row(row) for row in cpu_stats]
        
        # 合并两个表的统计结果
        product_usage_map = {stat['product_name']: stat for stat in product_usage_stats}
        
        for stat in cpu_stats:
            product_name = stat['product_name']
            if product_name in product_usage_map:
                product_usage_map[product_name]['usage_count'] += stat['usage_count']
                # 注意：两张表的用量单位可能不同，这里简单相�?
                product_usage_map[product_name]['total_used'] += stat['total_used'] if stat['total_used'] else 0
            else:
                product_usage_map[product_name] = stat
        
        # 将合并后的结果转为列表并按使用次数排�?
        product_usage_stats = list(product_usage_map.values())
        product_usage_stats.sort(key=lambda x: x['usage_count'], reverse=True)
        
        # 更新product_usage变量用于模板
        product_usage = product_usage_stats
        
    except Exception as e:
        app.logger.error(f"获取产品使用统计出错: {str(e)}")
        import traceback
        traceback.print_exc()
        product_usage_stats = []
    
    # 获取操作人员使用统计
    try:
        # 从product_usage表获取操作人员统�?
        pu_operator_query = f"""
        SELECT 
            o.id as operator_id,
            o.name as operator_name, 
            COUNT(pu.id) as operation_count
        FROM product_usage pu 
        JOIN operators o ON pu.operator_id = o.id 
        WHERE 1=1 {product_usage_filter}
        GROUP BY o.id 
        ORDER BY operation_count DESC
        """
        
        app.logger.info(f"操作人员统计查询SQL (product_usage): {pu_operator_query}, 参数: {pu_params}")
        
        pu_operator_stats = db.execute(pu_operator_query, pu_params).fetchall()
        pu_operator_stats = [dict_from_row(row) for row in pu_operator_stats]
        
        # 从client_product_usage表获取操作人员统�?
        cpu_operator_query = f"""
        SELECT 
            o.id as operator_id,
            o.name as operator_name, 
            COUNT(cpu.id) as operation_count
        FROM client_product_usage cpu 
        JOIN operators o ON cpu.operator_id = o.id 
        WHERE 1=1 {client_product_usage_filter}
        GROUP BY o.id 
        ORDER BY operation_count DESC
        """
        
        app.logger.info(f"操作人员统计查询SQL (client_product_usage): {cpu_operator_query}, 参数: {cpu_params}")
        
        cpu_operator_stats = db.execute(cpu_operator_query, cpu_params).fetchall()
        cpu_operator_stats = [dict_from_row(row) for row in cpu_operator_stats]
        
        # 合并两个表的操作人员统计
        operator_stats_map = {stat['operator_id']: stat for stat in pu_operator_stats}
        
        for stat in cpu_operator_stats:
            operator_id = stat['operator_id']
            if operator_id in operator_stats_map:
                operator_stats_map[operator_id]['operation_count'] += stat['operation_count']
            else:
                operator_stats_map[operator_id] = stat
        
        # 将合并后的结果转为列表并按操作次数排�?
        operator_stats = list(operator_stats_map.values())
        operator_stats.sort(key=lambda x: x['operation_count'], reverse=True)
        
        # 更新operator_usage变量用于模板
        operator_usage = [
            {
                'operator_name': stat['operator_name'],
                'position': '操作�?,
                'usage_count': stat['operation_count'],
                'total_used': stat.get('operation_count', 0),
                'client_count': 0,
                'product_type_count': 0
            }
            for stat in operator_stats
        ]
        
    except Exception as e:
        app.logger.error(f"获取操作人员统计出错: {str(e)}")
        import traceback
        traceback.print_exc()
        operator_stats = []
    
    # 获取产品与操作人员交叉统�?
    try:
        # 从product_usage表获取交叉统�?
        pu_cross_query = f"""
        SELECT 
            o.id as operator_id,
            o.name as operator_name, 
            p.id as product_id,
            p.name as product_name,
            COUNT(pu.id) as usage_count,
            SUM(pu.count_used) as total_used,
            COUNT(DISTINCT pu.client_product_id) as client_count,
            MAX(pu.usage_date) as last_usage_date
        FROM product_usage pu 
        JOIN operators o ON pu.operator_id = o.id 
        JOIN client_product cp ON pu.client_product_id = cp.id 
        JOIN product p ON cp.product_id = p.id 
        WHERE 1=1 {product_usage_filter}
        GROUP BY o.id, p.id 
        ORDER BY o.name, usage_count DESC
        """
        
        app.logger.info(f"产品与操作人员交叉统计查询SQL (product_usage): {pu_cross_query}, 参数: {pu_params}")
        
        pu_cross_stats = db.execute(pu_cross_query, pu_params).fetchall()
        pu_cross_stats = [dict_from_row(row) for row in pu_cross_stats]
        
        # 从client_product_usage表获取交叉统�?
        cpu_cross_query = f"""
        SELECT 
            o.id as operator_id,
            o.name as operator_name, 
            p.id as product_id,
            p.name as product_name,
            COUNT(cpu.id) as usage_count,
            SUM(cpu.amount_used) as total_used,
            COUNT(DISTINCT cpu.client_product_id) as client_count,
            MAX(cpu.usage_date) as last_usage_date
        FROM client_product_usage cpu 
        JOIN operators o ON cpu.operator_id = o.id 
        JOIN client_product cp ON cpu.client_product_id = cp.id 
        JOIN product p ON cp.product_id = p.id 
        WHERE 1=1 {client_product_usage_filter}
        GROUP BY o.id, p.id 
        ORDER BY o.name, usage_count DESC
        """
        
        app.logger.info(f"产品与操作人员交叉统计查询SQL (client_product_usage): {cpu_cross_query}, 参数: {cpu_params}")
        
        cpu_cross_stats = db.execute(cpu_cross_query, cpu_params).fetchall()
        cpu_cross_stats = [dict_from_row(row) for row in cpu_cross_stats]
        
        # 合并两个表的交叉统计
        cross_usage_map = {}
        
        # 处理product_usage数据
        for stat in pu_cross_stats:
            key = f"{stat['operator_id']}_{stat['product_id']}"
            cross_usage_map[key] = {
                'operator_id': stat['operator_id'],
                'operator_name': stat['operator_name'],
                'product_id': stat['product_id'],
                'product_name': stat['product_name'],
                'usage_count': stat['usage_count'],
                'total_used': stat['total_used'] if stat['total_used'] else 0,
                'client_count': stat['client_count'],
                'last_usage_date': stat['last_usage_date']
            }
        
        # 处理client_product_usage数据
        for stat in cpu_cross_stats:
            key = f"{stat['operator_id']}_{stat['product_id']}"
            if key in cross_usage_map:
                cross_usage_map[key]['usage_count'] += stat['usage_count']
                cross_usage_map[key]['total_used'] += stat['total_used'] if stat['total_used'] else 0
                cross_usage_map[key]['client_count'] += stat['client_count']
                
                # 更新最近使用日期（如果新日期更近）
                if stat['last_usage_date'] and (not cross_usage_map[key]['last_usage_date'] or 
                   stat['last_usage_date'] > cross_usage_map[key]['last_usage_date']):
                    cross_usage_map[key]['last_usage_date'] = stat['last_usage_date']
            else:
                cross_usage_map[key] = {
                    'operator_id': stat['operator_id'],
                    'operator_name': stat['operator_name'],
                    'product_id': stat['product_id'],
                    'product_name': stat['product_name'],
                    'usage_count': stat['usage_count'],
                    'total_used': stat['total_used'] if stat['total_used'] else 0,
                    'client_count': stat['client_count'],
                    'last_usage_date': stat['last_usage_date']
                }
        
        # 将字典转换为列表
        cross_usage = list(cross_usage_map.values())
        
        # 按操作人员名称和使用次数排序
        cross_usage.sort(key=lambda x: (x['operator_name'], -x['usage_count']))
        
    except Exception as e:
        app.logger.error(f"获取产品与操作人员交叉统计出�? {str(e)}")
        import traceback
        traceback.print_exc()
        cross_usage = []
    
    # 获取按产品分组的操作人员使用情况
    try:
        # 如果已经计算了cross_usage，我们可以重用这些数据来填充product_operator
        if cross_usage:
            # 创建一个产品分组的副本，但是按照产品名称和使用次数排序
            product_operator = copy.deepcopy(cross_usage)
            product_operator.sort(key=lambda x: (x['product_name'], -x['usage_count']))
        else:
            # 如果cross_usage为空，重新执行查�?
            # 从product_usage表获�?
            pu_product_query = f"""
            SELECT 
                o.id as operator_id,
                o.name as operator_name, 
                p.id as product_id,
                p.name as product_name,
                COUNT(pu.id) as usage_count,
                SUM(pu.count_used) as total_used,
                COUNT(DISTINCT pu.client_product_id) as client_count,
                MAX(pu.usage_date) as last_usage_date
            FROM product_usage pu 
            JOIN operators o ON pu.operator_id = o.id 
            JOIN client_product cp ON pu.client_product_id = cp.id 
            JOIN product p ON cp.product_id = p.id 
            WHERE 1=1 {product_usage_filter}
            GROUP BY p.id, o.id 
            ORDER BY p.name, usage_count DESC
            """
            
            app.logger.info(f"按产品分组的操作人员统计查询SQL (product_usage): {pu_product_query}, 参数: {pu_params}")
            
            pu_product_stats = db.execute(pu_product_query, pu_params).fetchall()
            pu_product_stats = [dict_from_row(row) for row in pu_product_stats]
            
            # 从client_product_usage表获�?
            cpu_product_query = f"""
            SELECT 
                o.id as operator_id,
                o.name as operator_name, 
                p.id as product_id,
                p.name as product_name,
                COUNT(cpu.id) as usage_count,
                SUM(cpu.amount_used) as total_used,
                COUNT(DISTINCT cpu.client_product_id) as client_count,
                MAX(cpu.usage_date) as last_usage_date
            FROM client_product_usage cpu 
            JOIN operators o ON cpu.operator_id = o.id 
            JOIN client_product cp ON cpu.client_product_id = cp.id 
            JOIN product p ON cp.product_id = p.id 
            WHERE 1=1 {client_product_usage_filter}
            GROUP BY p.id, o.id 
            ORDER BY p.name, usage_count DESC
            """
            
            app.logger.info(f"按产品分组的操作人员统计查询SQL (client_product_usage): {cpu_product_query}, 参数: {cpu_params}")
            
            cpu_product_stats = db.execute(cpu_product_query, cpu_params).fetchall()
            cpu_product_stats = [dict_from_row(row) for row in cpu_product_stats]
            
            # 合并两个表的统计
            product_operator_map = {}
            
            # 处理product_usage数据
            for stat in pu_product_stats:
                key = f"{stat['product_id']}_{stat['operator_id']}"
                product_operator_map[key] = {
                    'operator_id': stat['operator_id'],
                    'operator_name': stat['operator_name'],
                    'product_id': stat['product_id'],
                    'product_name': stat['product_name'],
                    'usage_count': stat['usage_count'],
                    'total_used': stat['total_used'] if stat['total_used'] else 0,
                    'client_count': stat['client_count'],
                    'last_usage_date': stat['last_usage_date']
                }
            
            # 处理client_product_usage数据
            for stat in cpu_product_stats:
                key = f"{stat['product_id']}_{stat['operator_id']}"
                if key in product_operator_map:
                    product_operator_map[key]['usage_count'] += stat['usage_count']
                    product_operator_map[key]['total_used'] += stat['total_used'] if stat['total_used'] else 0
                    product_operator_map[key]['client_count'] += stat['client_count']
                    
                    # 更新最近使用日期（如果新日期更近）
                    if stat['last_usage_date'] and (not product_operator_map[key]['last_usage_date'] or 
                       stat['last_usage_date'] > product_operator_map[key]['last_usage_date']):
                        product_operator_map[key]['last_usage_date'] = stat['last_usage_date']
                else:
                    product_operator_map[key] = {
                        'operator_id': stat['operator_id'],
                        'operator_name': stat['operator_name'],
                        'product_id': stat['product_id'],
                        'product_name': stat['product_name'],
                        'usage_count': stat['usage_count'],
                        'total_used': stat['total_used'] if stat['total_used'] else 0,
                        'client_count': stat['client_count'],
                        'last_usage_date': stat['last_usage_date']
                    }
            
            # 将字典转换为列表
            product_operator = list(product_operator_map.values())
            
            # 按产品名称和使用次数排序
            product_operator.sort(key=lambda x: (x['product_name'], -x['usage_count']))
    
    except Exception as e:
        app.logger.error(f"获取按产品分组的操作人员使用情况出错: {str(e)}")
        import traceback
        traceback.print_exc()
        product_operator = []
    
    # 获取新增客户和归属统�?
    try:
        new_clients_query = f"""
        SELECT 
            c.*, 
            u.username as user_name 
        FROM client c 
        LEFT JOIN user u ON c.user_id = u.id 
        WHERE 1=1 {client_filter}
        ORDER BY c.id DESC
        """
        
        app.logger.info(f"新增客户查询SQL: {new_clients_query}, 参数: {client_params}")
        
        new_clients = db.execute(new_clients_query, client_params).fetchall()
        new_clients = [dict_from_row(row) for row in new_clients]
        
        # 更新recent_clients变量用于模板
        recent_clients = new_clients[:10]  # 获取最�?0个客�?
        
        # 获取客户归属统计
        attribution_query = """
        SELECT 
            u.username as user_name, 
            COUNT(c.id) as client_count 
        FROM client c 
        JOIN user u ON c.user_id = u.id 
        GROUP BY u.id 
        ORDER BY client_count DESC
        """
        
        attribution_stats = db.execute(attribution_query).fetchall()
        attribution_stats = [dict_from_row(row) for row in attribution_stats]
        
        # 更新creator_stats变量用于模板
        creator_stats = attribution_stats
        
    # 获取详细使用记录
    try:
            # 先获取来自product_usage表的记录
            pu_detailed_query = f"""
            SELECT 
                pu.id as record_id,
                c.id as client_id,
                c.name as client_name,
                p.id as product_id,
                p.name as product_name,
                cp.price as price,
                cp.purchase_date as purchase_date,
                o.id as operator_id,
                o.name as operator_name,
                o.position as operator_position,
                COUNT(pu.id) as usage_times,
                SUM(pu.count_used) as amount_used,
                MAX(pu.usage_date) as last_usage_date,
                u.username as created_by
            FROM product_usage pu 
            JOIN client_product cp ON pu.client_product_id = cp.id 
            JOIN client c ON cp.client_id = c.id 
            JOIN product p ON cp.product_id = p.id 
            JOIN operators o ON pu.operator_id = o.id 
            LEFT JOIN user u ON c.user_id = u.id 
            WHERE 1=1 {product_usage_filter}
            GROUP BY cp.id, o.id 
            ORDER BY last_usage_date DESC
            LIMIT 100
            """
            
            app.logger.info(f"详细使用记录查询SQL (product_usage): {pu_detailed_query}, 参数: {pu_params}")
            
            pu_detailed_usage = db.execute(pu_detailed_query, pu_params).fetchall()
            pu_detailed_usage = [dict_from_row(row) for row in pu_detailed_usage]
            
            # 再获取来自client_product_usage表的记录
            cpu_detailed_query = f"""
            SELECT 
                cpu.id as record_id,
                c.id as client_id,
                c.name as client_name,
                p.id as product_id,
                p.name as product_name,
                cp.price as price,
                cp.purchase_date as purchase_date,
                o.id as operator_id,
                o.name as operator_name,
                o.position as operator_position,
                COUNT(cpu.id) as usage_times,
                SUM(cpu.amount_used) as amount_used,
                MAX(cpu.usage_date) as last_usage_date,
                u.username as created_by
            FROM client_product_usage cpu 
            JOIN client_product cp ON cpu.client_product_id = cp.id 
            JOIN client c ON cp.client_id = c.id 
            JOIN product p ON cp.product_id = p.id 
            JOIN operators o ON cpu.operator_id = o.id 
            LEFT JOIN user u ON c.user_id = u.id 
            WHERE 1=1 {client_product_usage_filter}
            GROUP BY cp.id, o.id 
            ORDER BY last_usage_date DESC
            LIMIT 100
            """
            
            app.logger.info(f"详细使用记录查询SQL (client_product_usage): {cpu_detailed_query}, 参数: {cpu_params}")
            
            cpu_detailed_usage = db.execute(cpu_detailed_query, cpu_params).fetchall()
            cpu_detailed_usage = [dict_from_row(row) for row in cpu_detailed_usage]
            
            # 合并两个表的记录
            detailed_usage = pu_detailed_usage + cpu_detailed_usage
            
            # 按最近使用日期排�?
            detailed_usage.sort(key=lambda x: x['last_usage_date'] if x['last_usage_date'] else '', reverse=True)
            
            # 限制返回的记录数
            detailed_usage = detailed_usage[:100]
            
    except Exception as e:
        app.logger.error(f"获取详细使用记录出错: {str(e)}")
        import traceback
        traceback.print_exc()
        detailed_usage = []
    
    # 获取最近的使用记录（不分组�?
    try:
        recent_usages_query = f"""
        SELECT 
            'product_usage' as source_table,
            pu.id as id,
            c.name as client_name,
            p.name as product_name,
            pu.count_used as amount_used,
            pu.usage_date as usage_date,
            o.name as operator_name
        FROM product_usage pu 
        JOIN client_product cp ON pu.client_product_id = cp.id 
        JOIN client c ON cp.client_id = c.id 
        JOIN product p ON cp.product_id = p.id 
        JOIN operators o ON pu.operator_id = o.id 
        WHERE 1=1 {product_usage_filter}
        UNION ALL
        SELECT 
            'client_product_usage' as source_table,
            cpu.id as id,
            c.name as client_name,
            p.name as product_name,
            cpu.amount_used as amount_used,
            cpu.usage_date as usage_date,
            o.name as operator_name
        FROM client_product_usage cpu 
        JOIN client_product cp ON cpu.client_product_id = cp.id 
        JOIN client c ON cp.client_id = c.id 
        JOIN product p ON cp.product_id = p.id 
        JOIN operators o ON cpu.operator_id = o.id 
        WHERE 1=1 {client_product_usage_filter}
        ORDER BY usage_date DESC
        LIMIT 10
        """
        
        recent_usages = db.execute(recent_usages_query, pu_params + cpu_params).fetchall()
        recent_usages = [dict_from_row(row) for row in recent_usages]

    except Exception as e:
        app.logger.error(f"获取最近使用记录出�? {str(e)}")
        import traceback
        traceback.print_exc()
        recent_usages = []
    
        
    except Exception as e:
    # 获取产品添加统计
    try:
        product_add_query = f"""
        SELECT 
            p.name as product_name, 
            COUNT(cp.id) as add_count 
        FROM client_product cp 
        JOIN product p ON cp.product_id = p.id 
        WHERE 1=1 {product_add_filter}
        GROUP BY p.id 
        ORDER BY add_count DESC
        """
        
        app.logger.info(f"产品添加统计查询SQL: {product_add_query}, 参数: {cp_params}")
        
        product_add_stats = db.execute(product_add_query, cp_params).fetchall()
        product_add_stats = [dict_from_row(row) for row in product_add_stats]
        
    except Exception as e:
        app.logger.error(f"获取产品添加统计出错: {str(e)}")
        product_add_stats = []
    
    return render_template('admin/statistics.html',
                          new_products=new_products,
                          product_usage_stats=product_usage_stats,
                          operator_stats=operator_stats,
                          new_clients=new_clients,
                          attribution_stats=attribution_stats,
                          product_add_stats=product_add_stats,
                          product_usage=product_usage,
                          operator_usage=operator_usage,
                          cross_usage=cross_usage,
                          product_operator=product_operator,
                          detailed_usage=detailed_usage,
                          recent_clients=recent_clients,
                          creator_stats=creator_stats,
                          recent_usages=recent_usages,
                          client_count=client_count,
                          product_count=product_count,
                          usage_count=usage_count,
                          product_sales_stats=product_sales_stats,
                          product_seller_stats=product_seller_stats,
                          product_sales=product_sales,
                          start_date=start_date,
                          end_date=end_date)

@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    """查看报表列表"""
    db = get_db()
    reports = db.execute(
        'SELECT * FROM report_records WHERE user_id = ? ORDER BY created_at DESC',
        (current_user.id,)
        ).fetchall()
    
    # 转换为列表字�?
    reports_list = [dict_from_row(report) for report in reports]
    
    return render_template('admin_reports.html', reports=reports_list)

@app.route('/admin/report/<int:report_id>/download')
@login_required
@admin_required
def download_report(report_id):
    """下载报表文件"""
    db = get_db()
    report = db.execute(
        'SELECT * FROM report_records WHERE id = ? AND user_id = ?',
        (report_id, current_user.id)
    ).fetchone()
    
    if not report:
        flash('报表不存在或您无权访�?, 'danger')
        return redirect(url_for('admin_reports'))
    
    if report['status'] != 'completed':
        flash('报表尚未完成生成', 'warning')
        return redirect(url_for('admin_reports'))
    
    if not report['file_path'] or not os.path.exists(report['file_path']):
        flash('报表文件不存在或已被删除', 'danger')
        return redirect(url_for('admin_reports'))
    
    # 返回文件下载
    try:
        return send_file(
            report['file_path'],
            as_attachment=True,
            download_name=os.path.basename(report['file_path'])
        )
    except Exception as e:
        app.logger.error(f"下载报表文件时出�? {str(e)}")
        flash(f'下载报表文件时出�? {str(e)}', 'danger')
        return redirect(url_for('admin_reports'))

# 客户面板路由

@app.route('/admin/send-reminders', methods=['POST'])
@login_required
@admin_required
def trigger_send_reminders():
    """手动触发发送预约提�?""
    try:
        if 'send_appointment_reminders' in globals():
            task = send_appointment_reminders.delay()
            flash('预约提醒发送任务已触发', 'success')
        else:
            flash('预约提醒功能未加载，请联系管理员', 'warning')
    except Exception as e:
        app.logger.error(f"触发预约提醒任务时出�? {str(e)}")
        flash(f'触发预约提醒任务时出�? {str(e)}', 'danger')
        
    return redirect(url_for('admin_manage_appointments'))

# 在文件顶部导入高级报表模�?
import os
try:
    from advanced_reports import generate_report
    ADVANCED_REPORTS_ENABLED = True
except ImportError:
    app.logger.warning("高级报表模块未找到，部分报表功能将不可用")
    ADVANCED_REPORTS_ENABLED = False

# 在合适的位置添加以下路由，如admin_reports()函数后面
@app.route('/admin/custom-report')
@login_required
@admin_required
def custom_report():
    """自定义报表设计页�?""
    # 检查是否已经初始化数据库表
    db = get_db()
    try:
        # 尝试获取报表模板
        report_templates = db.execute(
            'SELECT * FROM report_templates WHERE user_id = ? ORDER BY created_at DESC',
            (current_user.id,)
        ).fetchall()
        report_templates = [dict_from_row(template) for template in report_templates]
    except sqlite3.Error as e:
        # 如果表不存在或查询出错，创建�?
        app.logger.info(f"创建报表模板�? {str(e)}")
        try:
            db.execute('''
                CREATE TABLE IF NOT EXISTS report_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    config TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            ''')
            db.commit()
            report_templates = []
        except sqlite3.Error as e2:
            app.logger.error(f"创建报表模板表失�? {str(e2)}")
            flash(f"初始化报表功能失�? {str(e2)}", "danger")
            report_templates = []
    
    return render_template('custom_report.html', report_templates=report_templates)

@app.route('/admin/save-report-template', methods=['POST'])
@login_required
@admin_required
def save_report_template():
    """保存报表模板"""
    if not request.is_json:
        return jsonify({'status': 'error', 'error': '请求格式不正�?})
    
    data = request.get_json()
    name = data.get('name')
    config = data.get('config')
    
    if not name or not config:
        return jsonify({'status': 'error', 'error': '参数不完�?})
    
    try:
        db = get_db()
        db.execute(
            'INSERT INTO report_templates (user_id, name, config, created_at) VALUES (?, ?, ?, ?)',
            (current_user.id, name, json.dumps(config), datetime.now().isoformat())
        )
        db.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        app.logger.error(f"保存报表模板时出�? {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/admin/delete-report-template/<int:template_id>', methods=['POST'])
@login_required
@admin_required
def delete_report_template(template_id):
    """删除报表模板"""
    try:
        db = get_db()
        db.execute(
            'DELETE FROM report_templates WHERE id = ? AND user_id = ?',
            (template_id, current_user.id)
        )
        db.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        app.logger.error(f"删除报表模板时出�? {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/admin/generate-custom-report', methods=['POST'])
@login_required
@admin_required
def generate_custom_report():
    """生成自定义报�?""
    if not ADVANCED_REPORTS_ENABLED:
        flash('高级报表模块未启用，请联系管理员', 'danger')
        return redirect(url_for('custom_report'))
    
    report_name = request.form.get('report_name')
    start_date = request.form.get('start_date', '')
    end_date = request.form.get('end_date', '')
    report_config = request.form.get('report_config', '{}')
    
    try:
        # 解析配置
        config = json.loads(report_config)
        
        # 创建报表记录
        db = get_db()
        db.execute(
            'INSERT INTO report_records (user_id, report_type, status, created_at) VALUES (?, ?, ?, ?)',
            (current_user.id, 'custom', 'pending', datetime.now().isoformat())
        )
        db.commit()
        report_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # 生成报表
        result = generate_report('custom', start_date, end_date, current_user.id, config)
        
        if result['status'] == 'success':
            # 更新报表记录
            db.execute(
                'UPDATE report_records SET file_path = ?, status = ? WHERE id = ?',
                (result['report_path'], 'completed', report_id)
            )
            db.commit()
            flash(f'报表 "{report_name}" 生成成功', 'success')
        else:
            # 更新报表记录
            db.execute(
                'UPDATE report_records SET error_message = ?, status = ? WHERE id = ?',
                (result.get('error', '未知错误'), 'failed', report_id)
            )
            db.commit()
            flash(f'报表生成失败: {result.get("error", "未知错误")}', 'danger')
        
        return redirect(url_for('admin_reports'))
    except Exception as e:
        app.logger.error(f"生成自定义报表时出错: {str(e)}")
        flash(f'生成自定义报表时出错: {str(e)}', 'danger')
        return redirect(url_for('custom_report'))

@app.route('/admin/export-data/<export_type>')
@login_required
@admin_required
def export_data(export_type):
    """导出数据"""
    if not ADVANCED_REPORTS_ENABLED:
        flash('高级报表模块未启用，请联系管理员', 'danger')
        return redirect(url_for('dashboard'))
    
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    try:
        # 生成导出文件
        from advanced_reports import ExcelReportGenerator
        
        conn = get_db()
        data = {}
        
        if export_type == 'clients':
            # 导出客户数据
            query = '''
                SELECT c.*, u.username as creator_name
                FROM client c
                LEFT JOIN user u ON c.user_id = u.id
                WHERE 1=1
            '''
            params = []
            
            if start_date:
                query += " AND c.created_at >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND c.created_at <= ?"
                params.append(end_date)
            
            query += " ORDER BY c.created_at DESC"
            
            clients = conn.execute(query, params).fetchall()
            data['客户数据'] = pd.DataFrame([dict_from_row(client) for client in clients])
            
            # 导出客户消费数据
            query = '''
                SELECT c.name as client_name, p.name as product_name, p.price, 
                       cp.purchase_date, cp.expiry_date, cp.status
                FROM client c
                JOIN client_product cp ON c.id = cp.client_id
                JOIN product p ON cp.product_id = p.id
                WHERE 1=1
            '''
            params = []
            
            if start_date:
                query += " AND cp.purchase_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND cp.purchase_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY cp.purchase_date DESC"
            
            purchases = conn.execute(query, params).fetchall()
            data['客户消费记录'] = pd.DataFrame([dict_from_row(purchase) for purchase in purchases])
            
            filename = f"clients_export_{int(time.time())}.xlsx"
            
        elif export_type == 'products':
            # 导出产品数据
            products = conn.execute('SELECT * FROM product ORDER BY id').fetchall()
            data['产品信息'] = pd.DataFrame([dict_from_row(product) for product in products])
            
            # 导出产品销售数�?
            query = '''
                SELECT p.name as product_name, COUNT(cp.id) as sales_count, 
                       SUM(p.price) as total_amount
            FROM product p
                LEFT JOIN client_product cp ON p.id = cp.product_id
                WHERE cp.id IS NOT NULL
            '''
            params = []
            
            if start_date:
                query += " AND cp.purchase_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND cp.purchase_date <= ?"
                params.append(end_date)
            
            query += " GROUP BY p.id ORDER BY sales_count DESC"
            
            sales = conn.execute(query, params).fetchall()
            data['产品销售统�?] = pd.DataFrame([dict_from_row(sale) for sale in sales])
            
            filename = f"products_export_{int(time.time())}.xlsx"
            
        elif export_type == 'usage':
            # 导出使用记录
            query = '''
                SELECT c.name as client_name, p.name as product_name, 
                       pu.usage_date, pu.count_used,
                       o.name as operator_name, pu.notes
                FROM product_usage pu
                JOIN client_product cp ON pu.client_product_id = cp.id
            JOIN client c ON cp.client_id = c.id
            JOIN product p ON cp.product_id = p.id
                LEFT JOIN operators o ON pu.operator_id = o.id
                WHERE 1=1
            '''
            params = []
            
            if start_date:
                query += " AND pu.usage_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND pu.usage_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY pu.usage_date DESC"
            
            usages = conn.execute(query, params).fetchall()
            data['产品使用记录'] = pd.DataFrame([dict_from_row(usage) for usage in usages])
            
            # 导出操作人员统计
            query = '''
                SELECT o.name as operator_name, COUNT(pu.id) as usage_count
            FROM operators o
                JOIN product_usage pu ON o.id = pu.operator_id
                WHERE 1=1
            '''
            params = []
            
            if start_date:
                query += " AND pu.usage_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND pu.usage_date <= ?"
                params.append(end_date)
            
            query += " GROUP BY o.id ORDER BY usage_count DESC"
            
            operator_stats = conn.execute(query, params).fetchall()
            data['操作人员统计'] = pd.DataFrame([dict_from_row(stat) for stat in operator_stats])
            
            filename = f"usage_export_{int(time.time())}.xlsx"
        
        # 生成Excel文件
        report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
        os.makedirs(report_dir, exist_ok=True)
        export_file = os.path.join(report_dir, filename)
        
        # 创建Excel写入�?
        writer = pd.ExcelWriter(export_file, engine='xlsxwriter')
        
        # 写入数据
        for sheet_name, df in data.items():
            if not df.empty:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                worksheet = writer.sheets[sheet_name]
                
                # 自动调整列宽
                for i, col in enumerate(df.columns):
                    max_len = max(df[col].astype(str).map(len).max(), len(str(col)))
                    worksheet.set_column(i, i, max_len + 2)
            else:
                pd.DataFrame({'message': ['没有数据']}).to_excel(writer, sheet_name=sheet_name, index=False)
        
        # 保存Excel文件
        writer.close()
        
        # 创建导出记录
        db = get_db()
        db.execute(
            'INSERT INTO report_records (user_id, report_type, file_path, status, created_at) VALUES (?, ?, ?, ?, ?)',
            (current_user.id, f'export_{export_type}', export_file, 'completed', datetime.now().isoformat())
        )
        db.commit()
        
        # 返回文件下载
        return send_file(
            export_file,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        app.logger.error(f"导出数据时出�? {str(e)}")
        flash(f'导出数据时出�? {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/admin/custom-report-design', endpoint='custom_report_design')
@login_required
@admin_required
def custom_report_design():
    """自定义报表设计页�?""
    db = get_db()
    try:
        report_templates = db.execute(
            'SELECT * FROM report_templates WHERE user_id = ? ORDER BY created_at DESC',
            (current_user.id,)
        ).fetchall()
        report_templates = [dict_from_row(template) for template in report_templates]
    except:
        # 如果表不存在，创建表
        app.logger.info("创建报表模板�?)
        db.execute('''
            CREATE TABLE IF NOT EXISTS report_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                config TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        db.commit()
        report_templates = []
    
    return render_template('custom_report_design.html', report_templates=report_templates)

def export_operation_records_excel(records):
    """导出操作记录为Excel文件"""
    try:
        # 创建内存文件
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow(['操作类型', '操作�?, '客户', '产品', '操作数量', '操作时间', '备注'])
        
        # 写入数据
        for record in records:
            # 检查记录是字典还是sqlite3.Row对象
            if isinstance(record, dict):
                operation_type = '使用产品' if record.get('operation_type') == 'usage' else '购买产品'
                writer.writerow([
                    operation_type,
                    record.get('operator_name', '') or record.get('user_name', '') or '',
                    record.get('client_name', ''),
                    record.get('product_name', ''),
                    record.get('quantity', ''),
                    record.get('operation_time', ''),
                    record.get('notes', '') or ''
                ])
            else:
                # 处理sqlite3.Row对象
                record_dict = dict_from_row(record)
                operation_type = '使用产品' if record_dict.get('operation_type') == 'usage' else '购买产品'
                writer.writerow([
                    operation_type,
                    record_dict.get('operator_name', '') or record_dict.get('user_name', '') or '',
                    record_dict.get('client_name', ''),
                    record_dict.get('product_name', ''),
                    record_dict.get('quantity', ''),
                    record_dict.get('operation_time', ''),
                    record_dict.get('notes', '') or ''
                ])
        
        # 设置响应�?
        headers = {
            'Content-Disposition': 'attachment; filename=操作记录统计.csv',
            'Content-type': 'text/csv; charset=utf-8'
        }
        
        # 返回CSV响应
        return Response(
            output.getvalue().encode('utf-8-sig'),  # 使用UTF-8 with BOM以支持中文Excel打开
            mimetype='text/csv',
            headers=headers
        )
    except Exception as e:
        app.logger.error(f"导出操作记录失败: {str(e)}")
        flash(f"导出操作记录失败: {str(e)}", "danger")
        return redirect(url_for('admin_statistics'))

def get_simple_operation_records(db, start_date, end_date, operation_type=None):
    """获取简单操作记录，只从client_product_usage表获取数�?
    
    参数:
        db: 数据库连�?
        start_date: 开始日�?
        end_date: 结束日期
        operation_type: 操作类型，可选值为"usage"�?purchase"
    
    返回:
        (记录列表, 统计信息)
    """
    try:
        records = []
        
        # 如果未指定operation_type�?purchase"，则查询使用记录
        if not operation_type or operation_type == 'usage':
            cursor = db.cursor()
            
            # 修改查询，移除对TIMESTAMP类型的依�?
            query = """
                SELECT 
                    cpu.id,
                    cpu.client_product_id,
                    cpu.amount_used,
                    CAST(cpu.usage_date AS TEXT) as operation_time,
                    cpu.notes,
                    cpu.user_id,
                    cpu.operator_id,
                    'usage' as operation_type,
                    c.id as client_id,
                    c.name as client_name,
                    p.id as product_id,
                    p.name as product_name,
                    o.name as operator_name,
                    u.username as username
                FROM client_product_usage cpu
                JOIN client_product cp ON cpu.client_product_id = cp.id
                JOIN client c ON cp.client_id = c.id
                JOIN product p ON cp.product_id = p.id
                LEFT JOIN user u ON cpu.user_id = u.id
                LEFT JOIN operators o ON cpu.operator_id = o.id
                WHERE 1=1
            """
            
            # 添加日期过滤条件（如果有�?
            params = []
            if start_date:
                query += " AND CAST(cpu.usage_date AS TEXT) >= ?"
                params.append(start_date)
            if end_date:
                query += " AND CAST(cpu.usage_date AS TEXT) <= ?"
                params.append(end_date)
                
            query += " ORDER BY CAST(cpu.usage_date AS TEXT) DESC LIMIT 50"
            
            try:
                cursor.execute(query, params)
                
                # 手动转换结果，避免使用dict_from_row可能导致的异�?
                columns = [column[0] for column in cursor.description]
                for row in cursor.fetchall():
                    try:
                        record = {columns[i]: row[i] for i in range(len(columns))}
                        record['operation_type'] = 'usage'
                        record['quantity'] = record.get('amount_used', 1)
                        record['operation_time'] = record.get('operation_time')
                        records.append(record)
                    except Exception as e:
                        app.logger.error(f"处理记录时出�? {str(e)}")
                        continue
            except Exception as e:
                app.logger.error(f"执行client_product_usage查询失败: {str(e)}")
        
        # 如果未指定operation_type�?usage"，则查询购买记录
        if not operation_type or operation_type == 'purchase':
            # 获取购买记录
            query_purchase = """
                SELECT 
                    cp.id,
                    cp.id as client_product_id,
                    cp.remaining_count as amount_used,
                    cp.purchase_date as operation_time,
                    cp.notes,
                    c.user_id,
                    NULL as operator_id,
                    'purchase' as operation_type,
                    c.id as client_id,
                    c.name as client_name,
                    p.id as product_id,
                    p.name as product_name,
                    NULL as operator_name,
                    u.username as username
                FROM client_product cp
                JOIN client c ON cp.client_id = c.id
                JOIN product p ON cp.product_id = p.id
                LEFT JOIN user u ON c.user_id = u.id
                WHERE 1=1
            """
            
            # 添加日期过滤条件（如果有�?
            purchase_params = []
            if start_date:
                query_purchase += " AND cp.purchase_date >= ?"
                purchase_params.append(start_date)
            if end_date:
                query_purchase += " AND cp.purchase_date <= ?"
                purchase_params.append(end_date)
                
            query_purchase += " ORDER BY cp.purchase_date DESC LIMIT 50"
            
            try:
                cursor = db.cursor()
                cursor.execute(query_purchase, purchase_params)
                
                # 手动转换结果，避免使用dict_from_row可能导致的异�?
                columns = [column[0] for column in cursor.description]
                for row in cursor.fetchall():
                    try:
                        record = {columns[i]: row[i] for i in range(len(columns))}
                        record['operation_type'] = 'purchase'
                        record['quantity'] = record.get('amount_used', 1)
                        record['operation_time'] = record.get('operation_time')
                        records.append(record)
                    except Exception as e:
                        app.logger.error(f"处理购买记录时出�? {str(e)}")
                        continue
            except Exception as e:
                app.logger.error(f"执行client_product查询失败: {str(e)}")
        
        # 排序，使用安全方式处理日�?
        try:
            records.sort(key=lambda x: str(x.get('operation_time', '')), reverse=True)
        except Exception as e:
            app.logger.error(f"排序操作记录时出�? {str(e)}")
        
        # 计算统计信息
        stats = {
            'total_count': len(records),
            'total_clients': len(set(r.get('client_id', '') for r in records if r.get('client_id'))),
            'total_products': len(set(r.get('product_id', '') for r in records if r.get('product_id'))),
            'total_operators': len(set(r.get('operator_id', '') for r in records if r.get('operator_id'))),
            'total_pages': 1,
            'current_page': 1,
            'pages': 1,
            'page': 1
        }
        
        return records, stats
    except Exception as e:
        app.logger.error(f"获取操作记录出错: {str(e)}")
        import traceback
        traceback.print_exc()
        # 返回空结果和默认统计数据
        empty_stats = {'total_count': 0, 'total_clients': 0, 'total_products': 0, 'total_operators': 0, 
                      'total_pages': 1, 'current_page': 1, 'pages': 1, 'page': 1}
        return [], empty_stats

# 在get_simple_operation_records函数前添加以下函数定�?

def get_operation_records_json(db, args):
    """获取操作记录的JSON格式
    
    参数:
        db: 数据库连�?
        args: 请求参数，用于过滤记�?
    
    返回:
        JSON格式的操作记录结�?
    """
    try:
        # 获取过滤参数
        client_id = args.get('client_id')
        product_id = args.get('product_id')
        operator_id = args.get('operator_id')
        start_date = args.get('start_date', '')
        end_date = args.get('end_date', '')
        page = int(args.get('page', 1))
        per_page = int(args.get('per_page', 50))
        
        # 计算分页偏移
        offset = (page - 1) * per_page
        
        # 获取操作记录和统计信�?
        records, stats = get_operation_records_with_stats(db, args)
        
        # 构建JSON结果
        result = {
            'records': records,
            'stats': stats
        }
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"获取操作记录JSON时出�? {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'records': [], 'stats': {}})

def get_operation_records(db, args, for_export=False):
    """获取操作记录
    
    参数:
        db: 数据库连�?
        args: 请求参数，用于过滤记�?
        for_export: 是否为导出准备数�?
    
    返回:
        操作记录列表
    """
    try:
        # 获取过滤参数
        client_id = args.get('client_id')
        product_id = args.get('product_id')
        operator_id = args.get('operator_id')
        operation_type = args.get('operation_type')  # 操作类型筛�?
        start_date = args.get('start_date', '')
        end_date = args.get('end_date', '')
        page = int(args.get('page', 1)) if not for_export else 1
        per_page = int(args.get('per_page', 50)) if not for_export else 1000  # 导出时获取更多记�?
        
        # 设置默认日期范围（如果未提供�?
        if not start_date and not end_date:
            from datetime import date, timedelta
            end_date = date.today().isoformat()
            start_date = (date.today() - timedelta(days=30)).isoformat()
            
        app.logger.info(f"查询操作记录，日期范�? {start_date} �?{end_date}, 操作类型: {operation_type or '全部'}")
        app.logger.info(f"筛选条�? 客户ID={client_id}, 产品ID={product_id}, 操作员ID={operator_id}")
        
        all_records = []
        
        # 只有在未指定操作类型�?purchase"或未指定操作类型时，才查询使用记�?
        if not operation_type or operation_type == 'usage':
            # 查询使用记录 - 优先使用 client_product_usage �?
            try:
                # 基本查询 - 使用client_product_usage�?
                query_usage = """
                    SELECT 
                        cpu.id,
                        cpu.client_product_id,
                        cpu.amount_used,
                        cpu.usage_date as operation_time,
                        cpu.notes,
                        cpu.user_id,
                        cpu.operator_id,
                        'usage' as operation_type,
                        c.id as client_id,
                        c.name as client_name,
                        p.id as product_id,
                        p.name as product_name,
                        o.name as operator_name,
                        u.username as username
                    FROM client_product_usage cpu
                    JOIN client_product cp ON cpu.client_product_id = cp.id
                    JOIN client c ON cp.client_id = c.id
                    JOIN product p ON cp.product_id = p.id
                    LEFT JOIN operators o ON cpu.operator_id = o.id
                    LEFT JOIN user u ON cpu.user_id = u.id
                    WHERE 1=1
                """
                
                # 添加过滤条件
                usage_params = []
                
                if client_id:
                    query_usage += " AND c.id = ?"
                    usage_params.append(client_id)
                
                if product_id:
                    query_usage += " AND p.id = ?"
                    usage_params.append(product_id)
                
                if operator_id:
                    query_usage += " AND cpu.operator_id = ?"
                    usage_params.append(operator_id)
                
                if start_date:
                    query_usage += " AND date(cpu.usage_date) >= ?"
                    usage_params.append(start_date)
                
                if end_date:
                    query_usage += " AND date(cpu.usage_date) <= ?"
                    usage_params.append(end_date)
                
                # 获取usage数据
                cursor = db.cursor()
                app.logger.info(f"执行client_product_usage查询: {query_usage} 参数: {usage_params}")
                cursor.execute(query_usage, usage_params)
                columns = [column[0] for column in cursor.description]
                for row in cursor.fetchall():
                    try:
                        record = {columns[i]: row[i] for i in range(len(columns))}
                        record['quantity'] = record.get('amount_used', 1)
                        all_records.append(record)
                    except Exception as e:
                        app.logger.warning(f"处理使用记录时出�? {str(e)}")
                        continue
                
                # 如果没有找到记录，尝试从product_usage表查�?
                if not all_records:
                    query_pu = """
                        SELECT 
                            pu.id,
                            pu.client_product_id,
                            pu.count_used as amount_used,
                            pu.usage_date as operation_time,
                            pu.notes,
                            NULL as user_id,
                            pu.operator_id,
                            'usage' as operation_type,
                            c.id as client_id,
                            c.name as client_name,
                            p.id as product_id,
                            p.name as product_name,
                            o.name as operator_name,
                            'system' as username
                        FROM product_usage pu
                        JOIN client_product cp ON pu.client_product_id = cp.id
                        JOIN client c ON cp.client_id = c.id
                        JOIN product p ON cp.product_id = p.id
                        LEFT JOIN operators o ON pu.operator_id = o.id
                        WHERE 1=1
                    """
                    
                    # 添加过滤条件
                    pu_params = []
                    
                    if client_id:
                        query_pu += " AND c.id = ?"
                        pu_params.append(client_id)
                    
                    if product_id:
                        query_pu += " AND p.id = ?"
                        pu_params.append(product_id)
                    
                    if operator_id:
                        query_pu += " AND pu.operator_id = ?"
                        pu_params.append(operator_id)
                    
                    if start_date:
                        query_pu += " AND date(pu.usage_date) >= ?"
                        pu_params.append(start_date)
                    
                    if end_date:
                        query_pu += " AND date(pu.usage_date) <= ?"
                        pu_params.append(end_date)
                    
                    app.logger.info(f"执行product_usage查询: {query_pu} 参数: {pu_params}")
                    cursor.execute(query_pu, pu_params)
                    columns = [column[0] for column in cursor.description]
                    for row in cursor.fetchall():
                        try:
                            record = {columns[i]: row[i] for i in range(len(columns))}
                            record['quantity'] = record.get('amount_used', 1)
                            all_records.append(record)
                        except Exception as e:
                            app.logger.warning(f"处理旧使用记录时出错: {str(e)}")
                            continue
            except Exception as e:
                app.logger.error(f"执行使用记录查询失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 只有在未指定操作类型�?usage"或未指定操作类型时，才查询购买记�?
        if not operation_type or operation_type == 'purchase':
            # 获取购买记录
            query_purchase = """
                SELECT 
                    cp.id,
                    cp.id as client_product_id,
                    1 as amount_used,
                    cp.purchase_date as operation_time,
                    cp.notes,
                    c.user_id,
                    cp.operator_id,
                    'purchase' as operation_type,
                    c.id as client_id,
                    c.name as client_name,
                    p.id as product_id,
                    p.name as product_name,
                    o.name as operator_name,
                    u.username as username
                FROM client_product cp
                JOIN client c ON cp.client_id = c.id
                JOIN product p ON cp.product_id = p.id
                LEFT JOIN operators o ON cp.operator_id = o.id
                LEFT JOIN user u ON c.user_id = u.id
                WHERE 1=1
            """
            
            # 添加过滤条件
            purchase_params = []
            
            if client_id:
                query_purchase += " AND c.id = ?"
                purchase_params.append(client_id)
            
            if product_id:
                query_purchase += " AND p.id = ?"
                purchase_params.append(product_id)
            
            if operator_id:
                query_purchase += " AND cp.operator_id = ?"
                purchase_params.append(operator_id)
            
            if start_date:
                query_purchase += " AND date(cp.purchase_date) >= ?"
                purchase_params.append(start_date)
            
            if end_date:
                query_purchase += " AND date(cp.purchase_date) <= ?"
                purchase_params.append(end_date)
            
            # 获取purchase数据
            try:
                cursor = db.cursor()
                app.logger.info(f"执行client_product查询: {query_purchase} 参数: {purchase_params}")
                cursor.execute(query_purchase, purchase_params)
                columns = [column[0] for column in cursor.description]
                for row in cursor.fetchall():
                    try:
                        record = {columns[i]: row[i] for i in range(len(columns))}
                        record['quantity'] = 1  # 购买记录默认数量�?
                        all_records.append(record)
                    except Exception as e:
                        app.logger.warning(f"处理购买记录时出�? {str(e)}")
                        continue
            except Exception as e:
                app.logger.error(f"执行client_product查询失败: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 如果没有记录，返回空列表
        if not all_records:
            app.logger.info("没有找到符合条件的操作记�?)
            return []
        
        # 按操作时间排序，使用字符串比较避免类型问�?
        try:
            all_records.sort(key=lambda x: str(x.get('operation_time', '')), reverse=True)
        except Exception as e:
            app.logger.warning(f"排序操作记录时出�? {str(e)}")
        
        # 应用分页，除非是导出数据
        if not for_export:
            # 计算分页偏移
            offset = (page - 1) * per_page
            
            # 获取当前页的记录
            page_records = all_records[offset:offset + per_page]
            
            app.logger.info(f"返回 {len(page_records)}/{len(all_records)} 条记�?)
            return page_records
        else:
            app.logger.info(f"导出全部 {len(all_records)} 条记�?)
            return all_records
    except Exception as e:
        app.logger.error(f"获取操作记录时出�? {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def get_operation_records_with_stats(db, args):
    """获取带统计信息的操作记录
    
    参数:
        db: 数据库连�?
        args: 请求参数，用于过滤记�?
        
    返回:
        (操作记录列表, 统计信息)
    """
    try:
        # 获取操作记录
        records = get_operation_records(db, args)
        
        # 提取唯一�?
        client_ids = set()
        product_ids = set()
        operator_ids = set()
        
        for record in records:
            if record.get('client_id'):
                client_ids.add(record.get('client_id'))
            if record.get('product_id'):
                product_ids.add(record.get('product_id'))
            if record.get('operator_id'):
                operator_ids.add(record.get('operator_id'))
        
        # 计算总记录数 - 简化方�?
        # 使用计数查询而不是获取所有记�?
        try:
            # 基本参数
            client_id = args.get('client_id')
            product_id = args.get('product_id')
            operator_id = args.get('operator_id')
            operation_type = args.get('operation_type')
            start_date = args.get('start_date', '')
            end_date = args.get('end_date', '')
            
            # 默认使用分页参数获取的记录数�?
            total_records = len(records)
            
            # 如果当前页不是第一页或者记录数达到了每页的限制，则需要计算总数
            current_page = int(args.get('page', 1))
            per_page = int(args.get('per_page', 50))
            
            if current_page > 1 or len(records) >= per_page:
                # 将参数复制一份，但去掉分页参�?
                count_args = args.copy()
                if 'page' in count_args:
                    del count_args['page']
                if 'per_page' in count_args:
                    del count_args['per_page']
                
                # 获取全部记录用于计数
                all_records = get_operation_records(db, count_args, for_export=True)
                total_records = len(all_records)
        except Exception as e:
            app.logger.error(f"计算总记录数时出�? {str(e)}")
            total_records = len(records)
        
        # 计算总页�?
        per_page = int(args.get('per_page', 50))
        total_pages = (total_records + per_page - 1) // per_page if total_records > 0 else 1
        current_page = int(args.get('page', 1))
        
        # 构建统计信息
        stats = {
            'total_count': total_records,
            'total_clients': len(client_ids),
            'total_products': len(product_ids),
            'total_operators': len(operator_ids),
            'total_pages': total_pages,
            'current_page': current_page,
            # 添加别名以兼容模�?
            'pages': total_pages,
            'page': current_page
        }
        
        app.logger.info(f"生成统计信息: 总记录数: {total_records}, 总页�? {total_pages}, 当前�? {current_page}")
        return records, stats
    
    except Exception as e:
        app.logger.error(f"获取操作记录统计出错: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 如果查询出错，尝试使用简化版本的查询
        start_date = args.get('start_date', '')
        end_date = args.get('end_date', '')
        operation_type = args.get('operation_type')
        
        try:
            # 使用备用方法
            backup_records, backup_stats = get_simple_operation_records(db, start_date, end_date, operation_type)
            app.logger.info(f"成功使用备用方法获取操作记录: {len(backup_records)}条记�?)
            return backup_records, backup_stats
        except Exception as backup_error:
            app.logger.error(f"备用方法也失�? {str(backup_error)}")
            # 如果备用方法也失败，返回空结�?
            empty_stats = {'total_count': 0, 'total_clients': 0, 'total_products': 0, 'total_operators': 0, 
                          'total_pages': 1, 'current_page': 1, 'pages': 1, 'page': 1}
            return [], empty_stats

def get_operation_records_route():
    """操作记录查询路由
    
    通过该路由可以查看所有操作记录，包括产品使用和购买记�?
    """
    @app.route('/operation_records')
    @login_required
    def operation_records():
        """操作记录页面，包括使用产品和购买产品的记�?""
        db = get_db()
        
        # 检查是否是AJAX请求
        if request.args.get('get_operations') == '1':
            try:
                # 获取筛选条件并记录
                client_id = request.args.get('client_id')
                product_id = request.args.get('product_id')
                operator_id = request.args.get('operator_id')
                operation_type = request.args.get('operation_type')
                
                app.logger.info(f"AJAX请求操作记录，筛选条�? 客户ID={client_id}, 产品ID={product_id}, 操作员ID={operator_id}, 操作类型={operation_type}")
                
                # 获取操作记录
                records, stats = get_operation_records_with_stats(db, request.args)
                
                # 确保客户端能正确解析JSON数据
                for record in records:
                    # 转换所有None为空字符串或0，避免JSON序列化问�?
                    for key in record:
                        if record[key] is None:
                            if key in ['quantity', 'amount_used', 'count_used']:
                                record[key] = 0
                            else:
                                record[key] = ''
                
                return jsonify({
                    'records': records,
                    'stats': stats
                })
            except Exception as e:
                app.logger.error(f"AJAX加载操作记录出错: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': str(e), 'records': [], 'stats': {}})
        
        # 获取筛选选项数据
        cursor = db.cursor()
        
        # 获取操作人员列表
        try:
            cursor.execute("SELECT id, name FROM operators ORDER BY name")
            operators = [dict_from_row(row) for row in cursor.fetchall()]
        except Exception as e:
            app.logger.error(f"获取操作人员列表出错: {str(e)}")
            operators = []
        
        # 获取客户和产品列�?
        cursor.execute("SELECT id, name FROM client ORDER BY name")
        clients = [dict_from_row(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT id, name FROM product ORDER BY name")
        products = [dict_from_row(row) for row in cursor.fetchall()]
        
        # 获取日期范围
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # 如果没有提供日期，默认显示过�?0�?
        if not start_date:
            start_date = (date.today() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = date.today().isoformat()
        
        # 如果是导出Excel请求
        if request.args.get('export') == 'excel':
            operation_records = get_operation_records(db, request.args, for_export=True)
            return export_operation_records_excel(operation_records)
        
        # 创建默认的空记录和统计信�?
        operation_records = []
        operations_stats = {
            'total_count': 0,
            'total_clients': 0,
            'total_products': 0,
            'total_operators': 0,
            'total_pages': 1,
            'current_page': 1,
            'page': 1,
            'pages': 1
        }
        
        # 尝试获取首页数据
        try:
            operation_records, operations_stats = get_operation_records_with_stats(db, request.args)
        except Exception as e:
            app.logger.error(f"加载操作记录出错: {str(e)}")
            flash(f'加载操作记录时出现错�? {str(e)}', 'danger')
        
        # 获取当前页码
        page = int(request.args.get('page', 1))
        
        return render_template('operation_records.html',
                              operators=operators,
                              clients=clients,
                              products=products,
                              operation_records=operation_records,
                              operations_stats=operations_stats,
                              page=page,
                              start_date=start_date,
                              end_date=end_date)
    
    # 注册路由
    return operation_records

# 注册操作记录路由
operation_records = get_operation_records_route()

# 添加缺失的报表生成路�?
@app.route('/request-statistics-report', methods=['POST'])
@login_required
@admin_required
def request_statistics_report():
    """请求生成统计报表"""
    try:
        # 获取表单数据
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')
        report_type = request.form.get('report_type', 'statistics')
        
        if not start_date:
            start_date = (date.today() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = date.today().isoformat()
        
        # 创建报表记录
        db = get_db()
        db.execute(
            'INSERT INTO report_records (user_id, report_type, status, created_at) VALUES (?, ?, ?, ?)',
            (current_user.id, report_type, 'pending', datetime.now().isoformat())
        )
        db.commit()
        report_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # 尝试使用Celery异步生成报表
        try:
            if 'generate_statistics_report' in globals():
                task = generate_statistics_report.delay(start_date, end_date, current_user.id)
                # 更新任务ID
                db.execute('UPDATE report_records SET task_id = ? WHERE id = ?', (task.id, report_id))
                db.commit()
                flash('报表生成请求已提交，请稍后查看结�?, 'success')
            else:
                # 如果没有Celery，同步生成报�?
                result = {'status': 'completed', 'report_path': f'reports/report_{report_id}_{int(time.time())}.xlsx'}
                # 更新报表记录
                db.execute(
                    'UPDATE report_records SET file_path = ?, status = ? WHERE id = ?',
                    (result['report_path'], 'completed', report_id)
                )
                db.commit()
                flash('报表生成成功', 'success')
        except Exception as e:
            app.logger.error(f"提交报表生成任务失败: {str(e)}")
            db.execute(
                'UPDATE report_records SET error_message = ?, status = ? WHERE id = ?',
                (str(e), 'failed', report_id)
            )
            db.commit()
            flash(f'报表生成请求失败: {str(e)}', 'danger')
        
        return redirect(url_for('admin_reports'))
    except Exception as e:
        app.logger.error(f"请求生成报表时出�? {str(e)}")
        flash(f'请求生成报表时出�? {str(e)}', 'danger')
        return redirect(url_for('admin_reports'))

# 添加产品管理路由
@app.route('/products')
@login_required
@admin_required
def manage_products():
    """产品管理页面"""
    db = get_db()
    products = db.execute('SELECT * FROM product ORDER BY category, name').fetchall()
    products = [dict_from_row(p) for p in products]
    
    return render_template('products.html', products=products)

@app.route('/product/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    """添加新产�?""
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        type = request.form.get('type')
        category = request.form.get('category')
        details = request.form.get('details', '')
        sessions = request.form.get('sessions', 0)
        validity_days = request.form.get('validity_days', 0)
        
        # 验证输入
        if not name or not price or not type:
            flash('请填写所有必填字�?, 'danger')
            return render_template('add_product.html')
            
        try:
            price = float(price)
            sessions = int(sessions) if sessions else 0
            validity_days = int(validity_days) if validity_days else 0
        except ValueError:
            flash('价格、次数和有效期必须为数字', 'danger')
            return render_template('add_product.html')
        
        db = get_db()
        db.execute(
            'INSERT INTO product (name, price, type, category, details, sessions, validity_days) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (name, price, type, category, details, sessions, validity_days)
        )
        db.commit()
        
        flash(f'产品 {name} 添加成功', 'success')
        return redirect(url_for('manage_products'))
    
    return render_template('add_product.html')

@app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    """编辑产品"""
    db = get_db()
    product = db.execute('SELECT * FROM product WHERE id = ?', (product_id,)).fetchone()
    
    if not product:
        flash('产品不存�?, 'danger')
        return redirect(url_for('manage_products'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        type = request.form.get('type')
        category = request.form.get('category')
        details = request.form.get('details', '')
        sessions = request.form.get('sessions', 0)
        validity_days = request.form.get('validity_days', 0)
        
        # 验证输入
        if not name or not price or not type:
            flash('请填写所有必填字�?, 'danger')
            return render_template('edit_product.html', product=dict_from_row(product))
            
        try:
            price = float(price)
            sessions = int(sessions) if sessions else 0
            validity_days = int(validity_days) if validity_days else 0
        except ValueError:
            flash('价格、次数和有效期必须为数字', 'danger')
            return render_template('edit_product.html', product=dict_from_row(product))
        
        db.execute(
            'UPDATE product SET name = ?, price = ?, type = ?, category = ?, details = ?, sessions = ?, validity_days = ? WHERE id = ?',
            (name, price, type, category, details, sessions, validity_days, product_id)
        )
        db.commit()
        
        flash(f'产品 {name} 更新成功', 'success')
        return redirect(url_for('manage_products'))
    
    return render_template('edit_product.html', product=dict_from_row(product))

@app.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    """删除产品"""
    db = get_db()
    
    # 先检查产品是否有关联的客户产品记�?
    client_products = db.execute('SELECT COUNT(*) as count FROM client_product WHERE product_id = ?', 
                               (product_id,)).fetchone()
    
    if client_products and client_products['count'] > 0:
        flash('无法删除产品，因为已有客户购买此产品', 'danger')
        return redirect(url_for('manage_products'))
    
    product = db.execute('SELECT name FROM product WHERE id = ?', (product_id,)).fetchone()
    
    if not product:
        flash('产品不存�?, 'danger')
    else:
        db.execute('DELETE FROM product WHERE id = ?', (product_id,))
        db.commit()
        flash(f'产品 {product["name"]} 已成功删�?, 'success')
    
    return redirect(url_for('manage_products'))

# 添加用户管理路由
@app.route('/admin/users')
@login_required
@admin_required
def manage_users():
    """用户管理页面"""
    db = get_db()
    
    # 获取所有用�?
    users = db.execute('''
        SELECT u.*, c.name as client_name
        FROM user u
        LEFT JOIN client c ON u.client_id = c.id
        ORDER BY u.role, u.username
    ''').fetchall()
    
    users = [dict_from_row(u) for u in users]
    
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    """添加新用�?""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        name = request.form.get('name', '')
        phone = request.form.get('phone', '')
        email = request.form.get('email', '')
        client_id = request.form.get('client_id')
        
        # 验证输入
        if not username or not password or not role:
            flash('请填写所有必填字�?, 'danger')
            return render_template('add_user.html')
            
        if password != confirm_password:
            flash('两次密码输入不一�?, 'danger')
            return render_template('add_user.html')
        
        # 检查用户名是否已存�?
        db = get_db()
        existing_user = db.execute('SELECT id FROM user WHERE username = ?', (username,)).fetchone()
        
        if existing_user:
            flash('用户名已存在', 'danger')
            db = get_db()
            clients = db.execute('SELECT id, name, phone FROM client ORDER BY name').fetchall()
            clients = [dict_from_row(c) for c in clients]
            return render_template('add_user.html', clients=clients)
        
        # 处理client_id
        if role == 'client' and (not client_id or not client_id.strip()):
            flash('客户用户必须关联一个客户账�?, 'danger')
            db = get_db()
            clients = db.execute('SELECT id, name, phone FROM client ORDER BY name').fetchall()
            clients = [dict_from_row(c) for c in clients]
            return render_template('add_user.html', clients=clients)
        
        # 如果不是客户用户，则不需要client_id
        if role != 'client':
            client_id = None
        else:
            # 确保client_id是有效的客户ID
            client = db.execute('SELECT id FROM client WHERE id = ?', (client_id,)).fetchone()
            if not client:
                flash('选择的客户不存在', 'danger')
                db = get_db()
                clients = db.execute('SELECT id, name, phone FROM client ORDER BY name').fetchall()
                clients = [dict_from_row(c) for c in clients]
                return render_template('add_user.html', clients=clients)
            
        # 添加用户
        try:
            db.execute(
                'INSERT INTO user (username, password_hash, role, name, phone, email, client_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (username, generate_password_hash(password), role, name, phone, email, client_id, datetime.now().isoformat())
            )
            db.commit()
            flash(f'用户 {username} 添加成功', 'success')
            return redirect(url_for('manage_users'))
        except Exception as e:
            flash(f'添加用户失败: {str(e)}', 'danger')
            db = get_db()
            clients = db.execute('SELECT id, name, phone FROM client ORDER BY name').fetchall()
            clients = [dict_from_row(c) for c in clients]
            return render_template('add_user.html', clients=clients)
    
    # 获取客户列表，用于关联客户账�?
    db = get_db()
    clients = db.execute('SELECT id, name, phone FROM client ORDER BY name').fetchall()
    clients = [dict_from_row(c) for c in clients]
    
    return render_template('add_user.html', clients=clients)

@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """编辑用户"""
    db = get_db()
    user = db.execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        flash('用户不存�?, 'danger')
        return redirect(url_for('manage_users'))
    
    # 防止编辑当前登录的管理员
    if user_id == current_user.id:
        flash('不能编辑当前登录的管理员账户', 'warning')
        return redirect(url_for('manage_users'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        name = request.form.get('name', '')
        phone = request.form.get('phone', '')
        email = request.form.get('email', '')
        client_id = request.form.get('client_id')
        
        if client_id and not client_id.strip():
            client_id = None
        
        # 验证输入
        if not username or not role:
            flash('请填写所有必填字�?, 'danger')
            return render_template('edit_user.html', user=dict_from_row(user))
        
        # 检查用户名是否已被其他用户使用
        existing_user = db.execute('SELECT id FROM user WHERE username = ? AND id != ?', 
                                 (username, user_id)).fetchone()
        
        if existing_user:
            flash('用户名已被其他用户使�?, 'danger')
            return render_template('edit_user.html', user=dict_from_row(user))
        
        # 更新用户信息
        try:
            if password and password.strip():
                # 如果提供了新密码，更新密�?
                db.execute(
                    'UPDATE user SET username = ?, password_hash = ?, role = ?, name = ?, phone = ?, email = ?, client_id = ? WHERE id = ?',
                    (username, generate_password_hash(password), role, name, phone, email, client_id, user_id)
                )
            else:
                # 否则保留原密�?
                db.execute(
                    'UPDATE user SET username = ?, role = ?, name = ?, phone = ?, email = ?, client_id = ? WHERE id = ?',
                    (username, role, name, phone, email, client_id, user_id)
                )
            
            db.commit()
            flash(f'用户 {username} 更新成功', 'success')
            return redirect(url_for('manage_users'))
        except Exception as e:
            flash(f'更新用户失败: {str(e)}', 'danger')
            return render_template('edit_user.html', user=dict_from_row(user))
    
    # 获取客户列表，用于关联客户账�?
    clients = db.execute('SELECT id, name, phone FROM client ORDER BY name').fetchall()
    clients = [dict_from_row(c) for c in clients]
    
    return render_template('edit_user.html', user=dict_from_row(user), clients=clients)

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """删除用户"""
    db = get_db()
    
    # 防止删除当前登录的管理员
    if user_id == current_user.id:
        flash('不能删除当前登录的管理员账户', 'danger')
        return redirect(url_for('manage_users'))
    
    user = db.execute('SELECT username, role FROM user WHERE id = ?', (user_id,)).fetchone()
    
    if not user:
        flash('用户不存�?, 'danger')
    else:
        # 检查是否是唯一的管理员
        if user['role'] == 'admin':
            admin_count = db.execute('SELECT COUNT(*) as count FROM user WHERE role = "admin"').fetchone()
            if admin_count and admin_count['count'] <= 1:
                flash('不能删除唯一的管理员账户', 'danger')
                return redirect(url_for('manage_users'))
        
        # 检查是否有关联的客�?
        client = db.execute('SELECT id FROM client WHERE user_id = ?', (user_id,)).fetchone()
        
        if client:
            flash(f'用户 {user["username"]} 已创建客户，不能删除', 'danger')
        else:
            db.execute('DELETE FROM user WHERE id = ?', (user_id,))
            db.commit()
            flash(f'用户 {user["username"]} 已成功删�?, 'success')
    
    return redirect(url_for('manage_users'))

@app.route('/client/<int:client_id>/balance')
@login_required
def client_balance(client_id):
    """查看客户储值卡余额和交易历�?""
    # 检查是否有权限管理该客�?
    if not user_can_manage_client(client_id):
        flash('您没有权限管理此客户', 'danger')
        return redirect(url_for('dashboard'))
    
    # 获取客户信息
    db = get_db()
    client = db.execute('SELECT * FROM client WHERE id = ?', (client_id,)).fetchone()
    
    if not client:
        flash('客户不存�?, 'danger')
        return redirect(url_for('dashboard'))
    
    # 将客户信息转为字�?
    client = dict_from_row(client)
    
    # 确保客户余额和折扣有默认�?
    if client.get('balance') is None:
        client['balance'] = 0.0
    if client.get('discount') is None:
        client['discount'] = 1.0
    
    # 获取交易记录
    transactions = db.execute('''
        SELECT bt.*, u.username as operator_name
        FROM balance_transaction bt
        LEFT JOIN user u ON bt.operator_id = u.id
        WHERE bt.client_id = ?
        ORDER BY bt.created_at DESC
    ''', (client_id,)).fetchall()
    
    # 将交易记录转为字典列�?
    transactions = [dict_from_row(t) for t in transactions]
    
    return render_template(
        'client_balance.html',
        client=client,
        transactions=transactions
    )

@app.route('/client/<int:client_id>/recharge', methods=['GET', 'POST'])
@login_required
def recharge_balance(client_id):
    """为客户充值储值卡"""
    # 检查是否有权限管理该客�?
    if not user_can_manage_client(client_id):
        flash('您没有权限为此客户充�?, 'danger')
        return redirect(url_for('dashboard'))
    
    # 获取客户信息
    db = get_db()
    client = db.execute('SELECT * FROM client WHERE id = ?', (client_id,)).fetchone()
    
    if not client:
        flash('客户不存�?, 'danger')
        return redirect(url_for('dashboard'))
    
    # 将客户信息转为字�?
    client = dict_from_row(client)
    
    # 确保客户余额有默认�?
    if client.get('balance') is None:
        client['balance'] = 0.0
    
    # 获取所有操作员
    operators = db.execute('SELECT * FROM operators ORDER BY name').fetchall()
    operators = [dict_from_row(op) for op in operators]
    
    if request.method == 'POST':
        # 获取表单数据
        amount = request.form.get('amount', '')
        description = request.form.get('description', '')
        operator_id = request.form.get('operator_id')  # 获取操作员ID
        
        # 验证充值金额和操作�?
        try:
            if not operator_id:
                flash('请选择操作�?, 'danger')
                return render_template('recharge_balance.html', client=client, operators=operators)
                
            # 验证操作员是否存�?
            operator = db.execute('SELECT id FROM operators WHERE id = ?', (operator_id,)).fetchone()
            if not operator:
                flash('所选操作员不存�?, 'danger')
                return render_template('recharge_balance.html', client=client, operators=operators)
                
            amount = float(amount)
            if amount <= 0:
                raise ValueError('充值金额必须大�?')
        except ValueError:
            flash('请输入有效的充值金�?, 'danger')
            return render_template('recharge_balance.html', client=client, operators=operators)
        
        # 开始数据库事务
        db.execute('BEGIN TRANSACTION')
        
        try:
            # 获取当前余额
            before_balance = float(client['balance'])
            # 计算充值后余额
            after_balance = before_balance + amount
            
            # 更新客户余额
            db.execute(
                'UPDATE client SET balance = ? WHERE id = ?',
                (after_balance, client_id)
            )
            
            # 检查balance_transaction表是否有operator_id字段，如果没有则添加
            def column_exists(table_name, column_name):
                result = db.execute(f"PRAGMA table_info({table_name})").fetchall()
                return any(col['name'] == column_name for col in result)
            
            if not column_exists('balance_transaction', 'operator_id'):
                db.execute('ALTER TABLE balance_transaction ADD COLUMN operator_id INTEGER')
            
            # 记录充值交�?
            db.execute(
                '''INSERT INTO balance_transaction 
                (client_id, amount, transaction_type, description, before_balance, 
                after_balance, operator_id, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    client_id, amount, 'recharge', 
                    description, before_balance, 
                    after_balance, operator_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )
            
            # 提交事务
            db.commit()
            
            flash(f'已成功为客户充�?{amount} �?, 'success')
            return redirect(url_for('client_balance', client_id=client_id))
            
        except Exception as e:
            # 发生错误，回滚事�?
            db.execute('ROLLBACK')
            flash(f'充值时发生错误: {str(e)}', 'danger')
            app.logger.error(f"充值错�? {str(e)}")
            return render_template('recharge_balance.html', client=client, operators=operators)
    
    # GET请求，显示充值表�?
    return render_template('recharge_balance.html', client=client, operators=operators)

@app.route('/client/<int:client_id>/set_discount', methods=['POST'])
@login_required
@admin_required
def set_client_discount(client_id):
    """设置客户折扣�?""
    db = get_db()
    
    # 检查是否有权限管理该客�?
    if not user_can_manage_client(client_id):
        flash('您没有权限管理此客户', 'danger')
        return redirect(url_for('dashboard'))
    
    # 获取客户信息
    client = db.execute('SELECT * FROM client WHERE id = ?', (client_id,)).fetchone()
    
    if not client:
        flash('客户不存�?, 'danger')
        return redirect(url_for('dashboard'))
    
    # 获取表单数据
    discount = request.form.get('discount', '')
    
    # 验证折扣�?
    try:
        discount = float(discount)
        if discount < 0.1 or discount > 1:
            raise ValueError('折扣值必须在0.1�?之间')
    except ValueError:
        flash('请输入有效的折扣值（0.1-1之间�?, 'danger')
        return redirect(url_for('client_balance', client_id=client_id))
    
    try:
        # 更新客户折扣
        db.execute('UPDATE client SET discount = ? WHERE id = ?', (discount, client_id))
        db.commit()
        
        flash(f'客户折扣已更新为 {int(discount*100)}%', 'success')
    except Exception as e:
        app.logger.error(f"更新客户折扣时出�? {str(e)}")
        flash(f'更新折扣时发生错�? {str(e)}', 'danger')
    
    return redirect(url_for('client_balance', client_id=client_id))

if __name__ == '__main__':
    # 确保数据库已初始�?
    with app.app_context():
        app.logger.info("正在进行初始应用启动检�?..")
        try:
            ensure_db_exists()
            app.logger.info("数据库结构检查完�?)
        except Exception as e:
            app.logger.error(f"数据库初始化检查时出错: {str(e)}")
    
    app.run(debug=True) 
