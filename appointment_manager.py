#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
禾燃客户管理系统 - 预约管理模块
用于管理预约的专用模块，提供独立的访问点
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, g, session, jsonify
from flask_login import login_required, current_user
import sqlite3
from datetime import datetime
import functools

# 创建一个蓝图
appointment_bp = Blueprint('appointment', __name__, url_prefix='/appointment-manager')

# 数据库辅助函数
def get_db():
    """获取数据库连接"""
    if 'db' not in g:
        g.db = sqlite3.connect('database.db')
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """关闭数据库连接"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def dict_from_row(row):
    """将sqlite3.Row对象转换为字典"""
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}

# 管理员权限装饰器
def admin_required(view):
    """检查用户是否为管理员的装饰器，并且用户名必须为kevin"""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        
        # 从数据库查询用户信息
        db = get_db()
        user = db.execute('SELECT role, username FROM user WHERE id = ?', (current_user.id,)).fetchone()
        
        if not user or user['role'] != 'admin' or user['username'] != 'kevin':
            flash('此页面仅限管理员kevin访问', 'danger')
            return redirect(url_for('dashboard'))
            
        return view(**kwargs)
    return wrapped_view

# 预约管理主页
@appointment_bp.route('/')
@login_required
@admin_required
def index():
    """预约管理主页"""
    db = get_db()
    
    # 获取查询参数
    status_filter = request.args.get('status', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search_term = request.args.get('search', '')
    
    # 构建查询
    query = '''
        SELECT a.*, c.name as client_name, c.phone as client_phone,
               p.name as service_name
        FROM appointment a
        LEFT JOIN client c ON a.client_id = c.id
        LEFT JOIN client_product cp ON a.client_product_id = cp.id
        LEFT JOIN product p ON cp.product_id = p.id
    '''
    
    # 添加筛选条件
    conditions = []
    params = []
    
    if status_filter != 'all':
        conditions.append("a.status = ?")
        params.append(status_filter)
    
    if date_from:
        conditions.append("a.appointment_date >= ?")
        params.append(date_from)
    
    if date_to:
        conditions.append("a.appointment_date <= ?")
        params.append(date_to)
    
    if search_term:
        conditions.append("(c.name LIKE ? OR c.phone LIKE ?)")
        params.append(f"%{search_term}%")
        params.append(f"%{search_term}%")
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # 添加排序
    query += " ORDER BY a.appointment_date DESC, a.appointment_time ASC"
    
    # 执行查询
    appointments = db.execute(query, params).fetchall()
    
    # 转换为字典并按状态分类
    all_appointments = [dict_from_row(a) for a in appointments]
    
    pending_appointments = [a for a in all_appointments if a['status'] == 'pending']
    confirmed_appointments = [a for a in all_appointments if a['status'] == 'confirmed']
    completed_appointments = [a for a in all_appointments if a['status'] == 'completed']
    cancelled_appointments = [a for a in all_appointments if a['status'] == 'cancelled']
    
    return render_template(
        'manage_appointments.html',
        pending_appointments=pending_appointments,
        confirmed_appointments=confirmed_appointments,
        completed_appointments=completed_appointments,
        cancelled_appointments=cancelled_appointments,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to,
        search_term=search_term
    )

# 确认预约
@appointment_bp.route('/confirm/<int:appointment_id>', methods=['POST'])
@login_required
@admin_required
def confirm_appointment(appointment_id):
    """确认预约"""
    db = get_db()
    
    # 获取预约信息
    appointment = db.execute('SELECT * FROM appointment WHERE id = ? AND status = "pending"', (appointment_id,)).fetchone()
    
    if not appointment:
        flash('预约不存在或状态不正确', 'warning')
        return redirect(url_for('appointment.index'))
    
    # 更新预约状态为已确认
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
        # 例如发送短信或邮件通知客户预约已确认
        pass
    
    flash('预约已确认', 'success')
    return redirect(url_for('appointment.index'))

# 完成预约
@appointment_bp.route('/complete/<int:appointment_id>', methods=['POST'])
@login_required
@admin_required
def complete_appointment(appointment_id):
    """完成预约"""
    db = get_db()
    
    # 获取预约信息
    appointment = db.execute('SELECT * FROM appointment WHERE id = ? AND status = "confirmed"', (appointment_id,)).fetchone()
    
    if not appointment:
        flash('预约不存在或状态不正确', 'warning')
        return redirect(url_for('appointment.index'))
    
    # 更新预约状态为已完成
    now = datetime.now().isoformat()
    db.execute(
        'UPDATE appointment SET status = "completed", completed_time = ?, updated_at = ? WHERE id = ?',
        (now, now, appointment_id)
    )
    db.commit()
    
    # 如果预约使用了产品，处理产品使用记录
    client_product_id = appointment['client_product_id']
    if client_product_id:
        # 获取产品信息
        client_product = db.execute('SELECT * FROM client_product WHERE id = ?', (client_product_id,)).fetchone()
        
        # 如果是次数卡，减少剩余次数
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
    return redirect(url_for('appointment.index'))

# 取消预约
@appointment_bp.route('/cancel/<int:appointment_id>', methods=['POST'])
@login_required
@admin_required
def cancel_appointment(appointment_id):
    """取消预约"""
    cancel_reason = request.form.get('cancel_reason', '管理员取消')
    
    db = get_db()
    
    # 获取预约信息
    appointment = db.execute('SELECT * FROM appointment WHERE id = ? AND status IN ("pending", "confirmed")', (appointment_id,)).fetchone()
    
    if not appointment:
        flash('预约不存在或状态不正确', 'warning')
        return redirect(url_for('appointment.index'))
    
    # 更新预约状态为已取消
    now = datetime.now().isoformat()
    db.execute(
        'UPDATE appointment SET status = "cancelled", cancelled_time = ?, cancel_reason = ?, updated_at = ? WHERE id = ?',
        (now, cancel_reason, now, appointment_id)
    )
    db.commit()
    
    # 获取客户信息，用于发送通知
    client = db.execute('SELECT name, phone FROM client WHERE id = ?', (appointment['client_id'],)).fetchone()
    
    if client:
        # 这里可以添加发送取消通知的逻辑
        # 例如发送短信或邮件通知客户预约已取消
        pass
    
    flash('预约已取消', 'success')
    return redirect(url_for('appointment.index'))

# 视图预约详情
@appointment_bp.route('/view/<int:appointment_id>')
@login_required
@admin_required
def view_appointment(appointment_id):
    """查看预约详情"""
    db = get_db()
    
    # 获取预约信息
    appointment = db.execute('''
        SELECT a.*, c.name as client_name, c.phone as client_phone,
               p.name as service_name, cp.remaining_count, cp.expiry_date
        FROM appointment a
        LEFT JOIN client c ON a.client_id = c.id
        LEFT JOIN client_product cp ON a.client_product_id = cp.id
        LEFT JOIN product p ON cp.product_id = p.id
        WHERE a.id = ?
    ''', (appointment_id,)).fetchone()
    
    if not appointment:
        flash('预约不存在', 'warning')
        return redirect(url_for('appointment.index'))
    
    # 获取客户的其他预约记录
    client_appointments = db.execute('''
        SELECT a.*, p.name as service_name
        FROM appointment a
        LEFT JOIN client_product cp ON a.client_product_id = cp.id
        LEFT JOIN product p ON cp.product_id = p.id
        WHERE a.client_id = ? AND a.id != ?
        ORDER BY a.appointment_date DESC, a.appointment_time ASC
        LIMIT 5
    ''', (appointment['client_id'], appointment_id)).fetchall()
    
    return render_template(
        'appointment_detail.html',
        appointment=dict_from_row(appointment),
        client_appointments=[dict_from_row(a) for a in client_appointments]
    )

# 添加一个API端点，用于检查是否有新的预约
@appointment_bp.route('/check-new-appointments', methods=['GET'])
@login_required
@admin_required
def check_new_appointments():
    """检查是否有新的预约请求"""
    try:
        last_checked = session.get('last_appointment_check')
        current_time = datetime.now()
        
        # 如果是第一次检查，则设置当前时间为上次检查时间
        if not last_checked:
            session['last_appointment_check'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
            return jsonify({'new_appointments': 0})
        
        # 将字符串转换为datetime对象
        last_checked_time = datetime.strptime(last_checked, '%Y-%m-%d %H:%M:%S')
        
        # 获取新预约的数量
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM appointment WHERE created_at > ? AND status = 'pending'",
            (last_checked,)
        )
        new_appointment_count = cursor.fetchone()[0]
        
        # 更新最后检查时间
        session['last_appointment_check'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'new_appointments': new_appointment_count,
            'last_checked': last_checked,
            'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        app.logger.error(f"检查新预约时出错: {str(e)}")
        return jsonify({'error': str(e), 'new_appointments': 0})

@appointment_bp.route('/get-latest-appointments', methods=['GET'])
@login_required
@admin_required
def get_latest_appointments():
    """获取最新的预约列表，用于实时更新而无需刷新页面"""
    try:
        limit = request.args.get('limit', 5, type=int)
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT a.id, c.name, a.service_name, a.appointment_date, a.appointment_time, 
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
        app.logger.error(f"获取最新预约时出错: {str(e)}")
        return jsonify({'error': str(e), 'appointments': []})

# 当蓝图被注册到应用时，设置关闭数据库连接的回调
def init_app(app):
    app.teardown_appcontext(close_db) 