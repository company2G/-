#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
异步任务模块 - 禾燃客户管理系统
包含报表生成和通知发送等耗时任务
"""

import os
import time
from datetime import datetime, timedelta
import logging
import sqlite3
import pandas as pd
import xlsxwriter
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 获取数据库路径
def get_db_path():
    """获取数据库文件路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'database.db')

def get_db_connection():
    """获取数据库连接"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# 报表生成任务
def generate_statistics_report(start_date=None, end_date=None, user_id=None):
    """生成统计报表的异步任务"""
    logger.info(f"开始生成统计报表: 开始日期={start_date}, 结束日期={end_date}")
    
    try:
        # 创建报表目录
        report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
        os.makedirs(report_dir, exist_ok=True)
        
        # 生成报表文件名
        timestamp = int(time.time())
        report_file = os.path.join(report_dir, f'statistics_report_{timestamp}.xlsx')
        
        # 连接数据库
        conn = get_db_connection()
        
        # 构建SQL查询条件
        date_condition = ""
        params = []
        
        if start_date:
            date_condition += " AND cp.purchase_date >= ?"
            params.append(start_date)
        
        if end_date:
            date_condition += " AND cp.purchase_date <= ?"
            params.append(end_date)
        
        # 查询产品销售统计
        sales_stats = conn.execute('''
            SELECT 
                p.name as product_name,
                COUNT(cp.id) as sales_count,
                SUM(p.price) as total_amount,
                SUM(CASE WHEN p.type = 'count' THEN p.sessions ELSE 0 END) as total_sessions
            FROM product p
            LEFT JOIN client_product cp ON p.id = cp.product_id
            WHERE cp.id IS NOT NULL ''' + date_condition + '''
            GROUP BY p.id
            ORDER BY sales_count DESC
        ''', params).fetchall()
        
        # 查询客户统计
        client_stats = conn.execute('''
            SELECT 
                COUNT(*) as total_clients,
                SUM(CASE WHEN c.created_at >= ? THEN 1 ELSE 0 END) as new_clients
            FROM client c
        ''', (start_date or '1900-01-01',)).fetchone()
        
        # 查询预约统计
        appointment_stats = conn.execute('''
            SELECT 
                COUNT(*) as total_appointments,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_appointments,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_appointments
            FROM appointment
            WHERE 1=1
            ''' + (f"AND appointment_date >= '{start_date}'" if start_date else '') + '''
            ''' + (f"AND appointment_date <= '{end_date}'" if end_date else '') + '''
        ''').fetchone()
        
        # 转换为pandas DataFrame
        sales_df = pd.DataFrame([dict(row) for row in sales_stats])
        
        # 创建Excel文件
        writer = pd.ExcelWriter(report_file, engine='xlsxwriter')
        
        # 写入产品销售统计
        if not sales_df.empty:
            sales_df.to_excel(writer, sheet_name='产品销售统计', index=False)
        else:
            pd.DataFrame({'message': ['没有销售数据']}).to_excel(writer, sheet_name='产品销售统计', index=False)
        
        # 写入摘要统计
        summary_data = {
            '统计项目': ['总客户数', '新增客户数', '总预约数', '已完成预约数', '已取消预约数'],
            '数值': [
                client_stats['total_clients'],
                client_stats['new_clients'],
                appointment_stats['total_appointments'],
                appointment_stats['completed_appointments'],
                appointment_stats['cancelled_appointments']
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='摘要统计', index=False)
        
        # 获取产品销售明细
        product_sales = conn.execute('''
            SELECT 
                c.name as client_name,
                p.name as product_name,
                p.price,
                cp.purchase_date,
                cp.expiry_date,
                cp.remaining_count,
                cp.status
            FROM client_product cp
            JOIN client c ON cp.client_id = c.id
            JOIN product p ON cp.product_id = p.id
            WHERE 1=1 ''' + date_condition + '''
            ORDER BY cp.purchase_date DESC
        ''', params).fetchall()
        
        # 写入产品销售明细
        sales_detail_df = pd.DataFrame([dict(row) for row in product_sales])
        if not sales_detail_df.empty:
            sales_detail_df.to_excel(writer, sheet_name='销售明细', index=False)
        
        # 保存Excel文件
        writer.close()
        
        logger.info(f"统计报表生成成功: {report_file}")
        
        # 如果指定了用户ID，更新报表记录
        if user_id:
            conn.execute(
                'INSERT INTO report_records (user_id, report_type, file_path, status, created_at) VALUES (?, ?, ?, ?, ?)',
                (user_id, 'statistics', report_file, 'completed', datetime.now().isoformat())
            )
            conn.commit()
        
        conn.close()
        return {
            'status': 'success',
            'report_path': report_file
        }
        
    except Exception as e:
        logger.error(f"生成统计报表时出错: {str(e)}")
        
        # 如果指定了用户ID，记录错误
        if user_id:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO report_records (user_id, report_type, error_message, status, created_at) VALUES (?, ?, ?, ?, ?)',
                (user_id, 'statistics', str(e), 'failed', datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            
        return {
            'status': 'error',
            'error': str(e)
        }

# 发送通知任务
def send_notification(notification_type, recipient, subject, message, **kwargs):
    """发送通知的异步任务"""
    logger.info(f"开始发送通知: 类型={notification_type}, 接收者={recipient}")
    
    try:
        if notification_type == 'email':
            # 使用SMTP发送邮件
            # 邮件服务器配置
            smtp_server = kwargs.get('smtp_server', 'smtp.example.com')
            smtp_port = kwargs.get('smtp_port', 587)
            smtp_user = kwargs.get('smtp_user', 'user@example.com')
            smtp_password = kwargs.get('smtp_password', 'password')
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # 添加邮件内容
            msg.attach(MIMEText(message, 'html'))
            
            # 如果有附件
            attachment_path = kwargs.get('attachment')
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    attachment = MIMEApplication(f.read())
                    attachment.add_header(
                        'Content-Disposition', 
                        'attachment', 
                        filename=os.path.basename(attachment_path)
                    )
                    msg.attach(attachment)
            
            # 发送邮件
            try:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
                server.quit()
                logger.info("邮件发送成功")
                return {'status': 'success', 'type': 'email'}
            except Exception as e:
                logger.error(f"发送邮件时出错: {str(e)}")
                raise e
                
        elif notification_type == 'sms':
            # 这里需要集成短信API，例如阿里云、腾讯云等
            # 以下是示例代码，实际使用时需要替换为真实API
            logger.info("模拟发送短信...")
            logger.info(f"接收者: {recipient}")
            logger.info(f"内容: {message}")
            
            # 实际发送短信的代码，需要根据您使用的短信服务进行调整
            # import requests
            # response = requests.post(
            #     'https://api.example.com/sms',
            #     json={
            #         'apiKey': 'your-api-key',
            #         'mobile': recipient,
            #         'content': message,
            #         'templateId': kwargs.get('template_id')
            #     }
            # )
            # if response.status_code == 200:
            #     return {'status': 'success', 'type': 'sms'}
            # else:
            #     raise Exception(f"短信发送失败: {response.text}")
            
            # 这里只是模拟成功返回
            return {'status': 'success', 'type': 'sms'}
        
        else:
            raise ValueError(f"不支持的通知类型: {notification_type}")
            
    except Exception as e:
        logger.error(f"发送通知时出错: {str(e)}")
        return {'status': 'error', 'error': str(e)}

# 预约提醒任务
def send_appointment_reminders():
    """发送预约提醒的定时任务"""
    logger.info("开始发送预约提醒")
    
    try:
        conn = get_db_connection()
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 查询明天的预约
        appointments = conn.execute('''
        SELECT a.id, a.appointment_date, a.appointment_time, 
               c.id as client_id, c.name as client_name, c.phone as client_phone
        FROM appointment a
        JOIN client c ON a.client_id = c.id
        WHERE a.appointment_date = ? AND a.status = 'confirmed'
        ''', (tomorrow,)).fetchall()
        
        logger.info(f"找到 {len(appointments)} 个需要发送提醒的预约")
        
        for appointment in appointments:
            # 构建提醒消息
            message = f"尊敬的{appointment['client_name']}，提醒您明天{appointment['appointment_time']}有一个预约，请准时到达。"
            
            # 发送短信提醒
            send_notification(
                'sms', 
                appointment['client_phone'], 
                '预约提醒', 
                message
            )
                
            # 记录提醒发送
            conn.execute(
                'INSERT INTO notification_logs (client_id, appointment_id, type, content, status, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (appointment['client_id'], appointment['id'], 'sms', message, 'sent', datetime.now().isoformat())
            )
            
        conn.commit()
        conn.close()
        
        logger.info("预约提醒发送完成")
        return {'status': 'success', 'count': len(appointments)}
        
    except Exception as e:
        logger.error(f"发送预约提醒时出错: {str(e)}")
        return {'status': 'error', 'error': str(e)}

# 每日统计任务
def generate_daily_statistics():
    """生成每日统计报告的定时任务"""
    logger.info("开始生成每日统计报告")
    
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 生成昨日统计报告
        result = generate_statistics_report(yesterday, yesterday)
        
        if result['status'] == 'success':
            logger.info(f"每日统计报告生成成功: {result['report_path']}")
            
            # 可以在这里发送邮件通知管理员
            # send_notification(
            #     'email',
            #     'admin@example.com',
            #     f'每日统计报告 {yesterday}',
            #     f'请查看附件中的每日统计报告。',
            #     attachment=result['report_path']
            # )
        
        return {'status': 'success', 'report_path': result.get('report_path')}
        
    except Exception as e:
        logger.error(f"生成每日统计报告时出错: {str(e)}")
        return {'status': 'error', 'error': str(e)}

if __name__ == "__main__":
    # 测试生成报告
    print("测试生成统计报告...")
    result = generate_statistics_report()
    print(f"报告生成结果: {result}")
    
    # 测试发送通知
    print("\n测试发送通知...")
    result = send_notification('sms', '13800138000', '测试', '这是一条测试短信')
    print(f"通知发送结果: {result}") 