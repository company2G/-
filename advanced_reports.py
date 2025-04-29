#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
禾燃客户管理系统 - 高级报表模块
提供更全面的统计报表、数据导出和自定义报表功能
"""

import os
import time
import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import seaborn as sns
from io import BytesIO
import base64
import logging

# 创建日志记录器
logger = logging.getLogger("advanced_reports")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# 确保中文正确显示 - 需要配置合适的字体
# 在Windows系统中可以使用以下字体
font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'fonts', 'simhei.ttf')
if not os.path.exists(font_path):
    # 如果没有指定字体，尝试使用系统字体
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei']
        plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题
    except Exception as e:
        logger.warning(f"无法设置中文字体: {str(e)}")
else:
    # 注册自定义字体
    font_prop = FontProperties(fname=font_path)
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

def get_db_connection():
    """获取数据库连接"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

class ReportGenerator:
    """报表生成器基类, 提供基本报表功能"""
    
    def __init__(self, report_type, start_date=None, end_date=None, user_id=None, custom_params=None):
        """初始化报表生成器
        
        Args:
            report_type: 报表类型
            start_date: 开始日期
            end_date: 结束日期
            user_id: 用户ID
            custom_params: 自定义参数, 字典格式
        """
        self.report_type = report_type
        self.start_date = start_date
        self.end_date = end_date
        self.user_id = user_id
        self.custom_params = custom_params or {}
        self.timestamp = int(time.time())
        
        # 创建报表目录
        self.report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
        os.makedirs(self.report_dir, exist_ok=True)
        
        # 初始化数据结构
        self.report_data = {}
        self.charts = {}
    
    def generate(self):
        """生成报表"""
        try:
            # 收集数据
            self.collect_data()
            
            # 生成图表
            self.generate_charts()
            
            # 创建报表
            report_file = self.create_report()
            
            # 如果指定了用户ID, 更新报表记录
            if self.user_id:
                self.update_report_record(report_file)
            
            logger.info(f"报表生成成功: {report_file}")
            return {
                'status': 'success',
                'report_path': report_file
            }
        except Exception as e:
            logger.error(f"生成报表时出错: {str(e)}")
            
            # 如果指定了用户ID, 记录错误
            if self.user_id:
                self.record_error(str(e))
                
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def collect_data(self):
        """收集报表数据, 子类需要实现此方法"""
        raise NotImplementedError("子类必须实现此方法")
    
    def generate_charts(self):
        """生成报表图表, 子类需要实现此方法"""
        raise NotImplementedError("子类必须实现此方法")
    
    def create_report(self):
        """创建报表文件, 返回报表文件路径"""
        raise NotImplementedError("子类必须实现此方法")
    
    def update_report_record(self, report_file):
        """更新报表记录"""
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO report_records (user_id, report_type, file_path, status, created_at) VALUES (?, ?, ?, ?, ?)',
            (self.user_id, self.report_type, report_file, 'completed', datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    
    def record_error(self, error_message):
        """记录错误信息"""
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO report_records (user_id, report_type, error_message, status, created_at) VALUES (?, ?, ?, ?, ?)',
            (self.user_id, self.report_type, error_message, 'failed', datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    
    def get_date_condition(self):
        """获取日期条件SQL片段"""
        date_condition = ""
        params = []
        
        if self.start_date:
            date_condition += " AND created_at >= ?"
            params.append(self.start_date)
        
        if self.end_date:
            date_condition += " AND created_at <= ?"
            params.append(self.end_date)
        
        return date_condition, params

class ExcelReportGenerator(ReportGenerator):
    """Excel格式报表生成器"""
    
    def create_report(self):
        """创建Excel报表"""
        report_file = os.path.join(self.report_dir, f'{self.report_type}_report_{self.timestamp}.xlsx')
        
        # 创建Excel写入器
        writer = pd.ExcelWriter(report_file, engine='xlsxwriter')
        workbook = writer.book
        
        # 写入数据
        for sheet_name, data in self.report_data.items():
            if isinstance(data, pd.DataFrame):
                if not data.empty:
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
                    worksheet = writer.sheets[sheet_name]
                    
                    # 自动调整列宽
                    for i, col in enumerate(data.columns):
                        max_len = max(data[col].astype(str).map(len).max(), len(str(col)))
                        worksheet.set_column(i, i, max_len + 2)
                else:
                    pd.DataFrame({'message': ['没有数据']}).to_excel(writer, sheet_name=sheet_name, index=False)
        
        # 保存图表
        for sheet_name, chart_data in self.charts.items():
            if 'chart_bytes' in chart_data:
                worksheet = writer.book.add_worksheet(f"{sheet_name}_图表")
                image_data = BytesIO(chart_data['chart_bytes'])
                worksheet.insert_image('A1', 'chart.png', {'image_data': image_data})
                
                # 调整行高
                worksheet.set_row(0, 300)
                worksheet.set_column('A:A', 80)
        
        # 保存Excel文件
        writer.close()
        
        return report_file

class StatisticsReportGenerator(ExcelReportGenerator):
    """统计报表生成器"""
    
    def collect_data(self):
        """收集统计报表数据"""
        conn = get_db_connection()
        
        # 产品销售统计
        sales_stats_query = """
            SELECT 
                p.name as product_name,
                COUNT(cp.id) as sales_count,
                SUM(p.price) as total_amount,
                SUM(CASE WHEN p.type = 'count' THEN p.sessions ELSE 0 END) as total_sessions
            FROM product p
            LEFT JOIN client_product cp ON p.id = cp.product_id
            WHERE cp.id IS NOT NULL 
        """
        date_condition = ""
        params = []
        
        if self.start_date:
            date_condition += " AND cp.purchase_date >= ?"
            params.append(self.start_date)
        
        if self.end_date:
            date_condition += " AND cp.purchase_date <= ?"
            params.append(self.end_date)
        
        sales_stats_query += date_condition + " GROUP BY p.id ORDER BY sales_count DESC"
        sales_stats = conn.execute(sales_stats_query, params).fetchall()
        
        # 客户统计
        client_stats = conn.execute('''
            SELECT 
                COUNT(*) as total_clients,
                SUM(CASE WHEN created_at >= ? THEN 1 ELSE 0 END) as new_clients
            FROM client
        ''', (self.start_date or '1900-01-01',)).fetchone()
        
        # 预约统计
        appointment_query = """
            SELECT 
                COUNT(*) as total_appointments,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_appointments,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_appointments
            FROM appointment
            WHERE 1=1
        """
        
        appointment_params = []
        if self.start_date:
            appointment_query += " AND appointment_date >= ?"
            appointment_params.append(self.start_date)
        
        if self.end_date:
            appointment_query += " AND appointment_date <= ?"
            appointment_params.append(self.end_date)
        
        appointment_stats = conn.execute(appointment_query, appointment_params).fetchone()
        
        # 操作人员使用统计
        operator_stats_query = """
            SELECT 
                o.name as operator_name,
                COUNT(cpu.id) as total_usages,
                SUM(cpu.amount_used) as total_amount_used
            FROM operators o
            LEFT JOIN client_product_usage cpu ON o.id = cpu.operator_id
            WHERE cpu.id IS NOT NULL
        """
        
        operator_params = []
        if self.start_date:
            operator_stats_query += " AND cpu.usage_date >= ?"
            operator_params.append(self.start_date)
        
        if self.end_date:
            operator_stats_query += " AND cpu.usage_date <= ?"
            operator_params.append(self.end_date)
        
        operator_stats_query += " GROUP BY o.id ORDER BY total_usages DESC"
        operator_stats = conn.execute(operator_stats_query, operator_params).fetchall()
        
        # 产品销售明细
        product_sales_query = """
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
            WHERE 1=1
        """
        
        product_sales_query += date_condition + " ORDER BY cp.purchase_date DESC"
        product_sales = conn.execute(product_sales_query, params).fetchall()
        
        # 转换为DataFrame
        self.report_data = {
            '产品销售统计': pd.DataFrame([dict(row) for row in sales_stats]),
            '销售明细': pd.DataFrame([dict(row) for row in product_sales]),
            '操作人员统计': pd.DataFrame([dict(row) for row in operator_stats])
        }
        
        # 摘要统计
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
        
        self.report_data['摘要统计'] = pd.DataFrame(summary_data)
        
        conn.close()
    
    def generate_charts(self):
        """生成统计图表"""
        # 产品销售图表
        if '产品销售统计' in self.report_data and not self.report_data['产品销售统计'].empty:
            sales_df = self.report_data['产品销售统计']
            plt.figure(figsize=(12, 8))
            
            # 销售数量柱状图
            plt.subplot(2, 1, 1)
            sns.barplot(x='product_name', y='sales_count', data=sales_df.head(10))
            plt.title('产品销售数量TOP10')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # 销售金额柱状图
            plt.subplot(2, 1, 2)
            sns.barplot(x='product_name', y='total_amount', data=sales_df.head(10))
            plt.title('产品销售金额TOP10')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # 保存为二进制数据
            chart_bytes = BytesIO()
            plt.savefig(chart_bytes, format='png', dpi=100)
            chart_bytes.seek(0)
            
            self.charts['产品销售图表'] = {
                'chart_bytes': chart_bytes.getvalue()
            }
            plt.close()
        
        # 操作人员统计图表
        if '操作人员统计' in self.report_data and not self.report_data['操作人员统计'].empty:
            operator_df = self.report_data['操作人员统计']
            plt.figure(figsize=(12, 6))
            
            sns.barplot(x='operator_name', y='total_usages', data=operator_df)
            plt.title('操作人员服务次数统计')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # 保存为二进制数据
            chart_bytes = BytesIO()
            plt.savefig(chart_bytes, format='png', dpi=100)
            chart_bytes.seek(0)
            
            self.charts['操作人员统计图表'] = {
                'chart_bytes': chart_bytes.getvalue()
            }
            plt.close()

class SalesReportGenerator(ExcelReportGenerator):
    """销售报表生成器"""
    
    def collect_data(self):
        """收集销售报表数据"""
        conn = get_db_connection()
        
        # 销售总览
        date_condition, params = self.get_date_condition()
        date_condition = date_condition.replace("created_at", "cp.purchase_date")
        
        sales_overview_query = """
            SELECT 
                strftime('%Y-%m', cp.purchase_date) as month,
                COUNT(cp.id) as sales_count,
                SUM(p.price) as total_amount
            FROM client_product cp
            JOIN product p ON cp.product_id = p.id
            WHERE 1=1
        """
        
        sales_overview_query += date_condition + " GROUP BY month ORDER BY month"
        sales_overview = conn.execute(sales_overview_query, params).fetchall()
        
        # 产品类别销售
        category_sales_query = """
            SELECT 
                p.category,
                COUNT(cp.id) as sales_count,
                SUM(p.price) as total_amount
            FROM client_product cp
            JOIN product p ON cp.product_id = p.id
            WHERE 1=1
        """
        
        category_sales_query += date_condition + " GROUP BY p.category ORDER BY total_amount DESC"
        category_sales = conn.execute(category_sales_query, params).fetchall()
        
        # 产品明细销售
        product_sales_query = """
            SELECT 
                p.name as product_name,
                p.category,
                p.type,
                COUNT(cp.id) as sales_count,
                SUM(p.price) as total_amount,
                AVG(p.price) as avg_price
            FROM client_product cp
            JOIN product p ON cp.product_id = p.id
            WHERE 1=1
        """
        
        product_sales_query += date_condition + " GROUP BY p.id ORDER BY sales_count DESC"
        product_sales = conn.execute(product_sales_query, params).fetchall()
        
        # 销售明细
        sales_detail_query = """
            SELECT 
                cp.purchase_date,
                c.name as client_name,
                p.name as product_name,
                p.category,
                p.price,
                u.username as seller_name
            FROM client_product cp
            JOIN client c ON cp.client_id = c.id
            JOIN product p ON cp.product_id = p.id
            LEFT JOIN user u ON c.user_id = u.id
            WHERE 1=1
        """
        
        sales_detail_query += date_condition + " ORDER BY cp.purchase_date DESC"
        sales_detail = conn.execute(sales_detail_query, params).fetchall()
        
        # 转换为DataFrame
        self.report_data = {
            '销售月度总览': pd.DataFrame([dict(row) for row in sales_overview]),
            '产品类别销售': pd.DataFrame([dict(row) for row in category_sales]),
            '产品销售统计': pd.DataFrame([dict(row) for row in product_sales]),
            '销售明细': pd.DataFrame([dict(row) for row in sales_detail])
        }
        
        conn.close()
    
    def generate_charts(self):
        """生成销售图表"""
        # 月度销售趋势图
        if '销售月度总览' in self.report_data and not self.report_data['销售月度总览'].empty:
            trend_df = self.report_data['销售月度总览']
            plt.figure(figsize=(12, 6))
            
            plt.subplot(1, 2, 1)
            plt.plot(trend_df['month'], trend_df['sales_count'], marker='o')
            plt.title('月度销售数量趋势')
            plt.xticks(rotation=45)
            
            plt.subplot(1, 2, 2)
            plt.plot(trend_df['month'], trend_df['total_amount'], marker='o', color='orange')
            plt.title('月度销售金额趋势')
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            
            # 保存为二进制数据
            chart_bytes = BytesIO()
            plt.savefig(chart_bytes, format='png', dpi=100)
            chart_bytes.seek(0)
            
            self.charts['销售趋势图表'] = {
                'chart_bytes': chart_bytes.getvalue()
            }
            plt.close()
        
        # 产品类别销售图表
        if '产品类别销售' in self.report_data and not self.report_data['产品类别销售'].empty:
            category_df = self.report_data['产品类别销售']
            plt.figure(figsize=(12, 6))
            
            plt.subplot(1, 2, 1)
            plt.pie(category_df['sales_count'], labels=category_df['category'], autopct='%1.1f%%')
            plt.title('产品类别销售数量占比')
            
            plt.subplot(1, 2, 2)
            plt.pie(category_df['total_amount'], labels=category_df['category'], autopct='%1.1f%%')
            plt.title('产品类别销售金额占比')
            
            plt.tight_layout()
            
            # 保存为二进制数据
            chart_bytes = BytesIO()
            plt.savefig(chart_bytes, format='png', dpi=100)
            chart_bytes.seek(0)
            
            self.charts['类别销售图表'] = {
                'chart_bytes': chart_bytes.getvalue()
            }
            plt.close()

class ClientReportGenerator(ExcelReportGenerator):
    """客户报表生成器"""
    
    def collect_data(self):
        """收集客户报表数据"""
        conn = get_db_connection()
        
        # 客户增长趋势
        date_condition, params = self.get_date_condition()
        
        growth_query = """
            SELECT 
                strftime('%Y-%m', created_at) as month,
                COUNT(*) as new_clients
            FROM client
            WHERE 1=1
        """
        
        growth_query += date_condition + " GROUP BY month ORDER BY month"
        growth_data = conn.execute(growth_query, params).fetchall()
        
        # 客户消费统计
        client_consumption_query = """
            SELECT 
                c.name as client_name,
                COUNT(cp.id) as purchase_count,
                SUM(p.price) as total_amount,
                MAX(cp.purchase_date) as last_purchase_date
            FROM client c
            LEFT JOIN client_product cp ON c.id = cp.client_id
            LEFT JOIN product p ON cp.product_id = p.id
            WHERE cp.id IS NOT NULL
        """
        
        consumption_params = []
        consumption_date_condition = ""
        
        if self.start_date:
            consumption_date_condition += " AND cp.purchase_date >= ?"
            consumption_params.append(self.start_date)
        
        if self.end_date:
            consumption_date_condition += " AND cp.purchase_date <= ?"
            consumption_params.append(self.end_date)
        
        client_consumption_query += consumption_date_condition + " GROUP BY c.id ORDER BY total_amount DESC"
        client_consumption = conn.execute(client_consumption_query, consumption_params).fetchall()
        
        # 客户产品使用记录
        client_usage_query = """
            SELECT 
                c.name as client_name,
                p.name as product_name,
                SUM(cpu.amount_used) as usage_count,
                MAX(cpu.usage_date) as last_usage_date
            FROM client c
            JOIN client_product cp ON c.id = cp.client_id
            JOIN product p ON cp.product_id = p.id
            JOIN client_product_usage cpu ON cp.id = cpu.client_product_id
            WHERE 1=1
        """
        
        usage_params = []
        usage_date_condition = ""
        
        if self.start_date:
            usage_date_condition += " AND cpu.usage_date >= ?"
            usage_params.append(self.start_date)
        
        if self.end_date:
            usage_date_condition += " AND cpu.usage_date <= ?"
            usage_params.append(self.end_date)
        
        client_usage_query += usage_date_condition + " GROUP BY c.id, p.id ORDER BY c.id, usage_count DESC"
        client_usage = conn.execute(client_usage_query, usage_params).fetchall()
        
        # 转换为DataFrame
        self.report_data = {
            '客户增长趋势': pd.DataFrame([dict(row) for row in growth_data]),
            '客户消费统计': pd.DataFrame([dict(row) for row in client_consumption]),
            '客户产品使用': pd.DataFrame([dict(row) for row in client_usage])
        }
        
        # 客户明细（当前客户列表）
        client_detail_query = """
            SELECT 
                c.name, 
                c.phone, 
                c.address, 
                c.gender, 
                c.created_at, 
                u.username as creator_name
            FROM client c
            LEFT JOIN user u ON c.user_id = u.id
            WHERE 1=1
        """
        
        client_detail_query += date_condition + " ORDER BY c.created_at DESC"
        client_detail = conn.execute(client_detail_query, params).fetchall()
        self.report_data['客户明细'] = pd.DataFrame([dict(row) for row in client_detail])
        
        conn.close()
    
    def generate_charts(self):
        """生成客户图表"""
        # 客户增长趋势图
        if '客户增长趋势' in self.report_data and not self.report_data['客户增长趋势'].empty:
            growth_df = self.report_data['客户增长趋势']
            plt.figure(figsize=(12, 6))
            
            # 月度新增客户数
            plt.bar(growth_df['month'], growth_df['new_clients'], color='skyblue')
            plt.title('月度新增客户数')
            plt.xlabel('月份')
            plt.ylabel('新增客户数')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # 保存为二进制数据
            chart_bytes = BytesIO()
            plt.savefig(chart_bytes, format='png', dpi=100)
            chart_bytes.seek(0)
            
            self.charts['客户增长趋势图'] = {
                'chart_bytes': chart_bytes.getvalue()
            }
            plt.close()
        
        # 客户消费TOP10图表
        if '客户消费统计' in self.report_data and not self.report_data['客户消费统计'].empty:
            consumption_df = self.report_data['客户消费统计'].head(10)
            plt.figure(figsize=(12, 6))
            
            plt.bar(consumption_df['client_name'], consumption_df['total_amount'], color='orange')
            plt.title('客户消费TOP10')
            plt.xlabel('客户')
            plt.ylabel('消费金额')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # 保存为二进制数据
            chart_bytes = BytesIO()
            plt.savefig(chart_bytes, format='png', dpi=100)
            chart_bytes.seek(0)
            
            self.charts['客户消费TOP10'] = {
                'chart_bytes': chart_bytes.getvalue()
            }
            plt.close()

class CustomReportGenerator(ExcelReportGenerator):
    """自定义报表生成器"""
    
    def collect_data(self):
        """根据自定义参数收集报表数据"""
        try:
            conn = get_db_connection()
            
            # 从自定义参数中获取查询信息
            report_tables = self.custom_params.get('tables', [])
            
            # 对每个表执行查询
            for table_config in report_tables:
                table_name = table_config.get('table_name')
                fields = table_config.get('fields', ['*'])
                filters = table_config.get('filters', {})
                joins = table_config.get('joins', [])
                group_by = table_config.get('group_by', [])
                order_by = table_config.get('order_by', {})
                
                # 构建SQL查询
                fields_str = ', '.join(fields) if fields != ['*'] else '*'
                sql = f"SELECT {fields_str} FROM {table_name}"
                
                # 添加连接
                for join in joins:
                    join_type = join.get('type', 'LEFT JOIN')
                    join_table = join.get('table')
                    join_on = join.get('on')
                    sql += f" {join_type} {join_table} ON {join_on}"
                
                # 添加过滤条件
                where_clauses = []
                where_params = []
                
                # 添加日期筛选
                date_field = table_config.get('date_field')
                if date_field and (self.start_date or self.end_date):
                    if self.start_date:
                        where_clauses.append(f"{date_field} >= ?")
                        where_params.append(self.start_date)
                    if self.end_date:
                        where_clauses.append(f"{date_field} <= ?")
                        where_params.append(self.end_date)
                
                # 添加自定义过滤条件
                for field, condition in filters.items():
                    operator = condition.get('operator', '=')
                    value = condition.get('value')
                    
                    if value is not None:
                        where_clauses.append(f"{field} {operator} ?")
                        where_params.append(value)
                
                if where_clauses:
                    sql += " WHERE " + " AND ".join(where_clauses)
                
                # 添加分组
                if group_by:
                    sql += " GROUP BY " + ", ".join(group_by)
                
                # 添加排序
                if order_by:
                    order_clauses = []
                    for field, direction in order_by.items():
                        order_clauses.append(f"{field} {direction}")
                    sql += " ORDER BY " + ", ".join(order_clauses)
                
                # 执行查询
                results = conn.execute(sql, where_params).fetchall()
                
                # 构建DataFrame
                sheet_name = table_config.get('label', table_name)
                self.report_data[sheet_name] = pd.DataFrame([dict(row) for row in results])
            
            conn.close()
        except Exception as e:
            logger.error(f"自定义报表数据收集错误: {str(e)}")
            self.report_data = {
                '错误信息': pd.DataFrame({'错误': [str(e)]})
            }
    
    def generate_charts(self):
        """根据自定义参数生成图表"""
        # 从自定义参数中获取图表配置
        chart_configs = self.custom_params.get('charts', [])
        
        for chart_config in chart_configs:
            try:
                chart_type = chart_config.get('type', 'bar')
                data_source = chart_config.get('data_source')
                chart_title = chart_config.get('title', '自定义图表')
                x_field = chart_config.get('x_field')
                y_field = chart_config.get('y_field')
                
                # 确保数据源存在
                if data_source not in self.report_data or x_field not in self.report_data[data_source].columns:
                    continue
                
                data = self.report_data[data_source]
                
                plt.figure(figsize=(12, 6))
                
                if chart_type == 'bar':
                    plt.bar(data[x_field], data[y_field])
                elif chart_type == 'line':
                    plt.plot(data[x_field], data[y_field], marker='o')
                elif chart_type == 'pie':
                    plt.pie(data[y_field], labels=data[x_field], autopct='%1.1f%%')
                
                plt.title(chart_title)
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                
                # 保存为二进制数据
                chart_bytes = BytesIO()
                plt.savefig(chart_bytes, format='png', dpi=100)
                chart_bytes.seek(0)
                
                self.charts[chart_title] = {
                    'chart_bytes': chart_bytes.getvalue()
                }
                plt.close()
            except Exception as e:
                logger.error(f"自定义图表生成错误: {str(e)}")

def generate_report(report_type, start_date=None, end_date=None, user_id=None, custom_params=None):
    """根据类型生成报表"""
    # 选择报表生成器
    if report_type == 'statistics':
        generator = StatisticsReportGenerator(report_type, start_date, end_date, user_id)
    elif report_type == 'sales':
        generator = SalesReportGenerator(report_type, start_date, end_date, user_id)
    elif report_type == 'clients':
        generator = ClientReportGenerator(report_type, start_date, end_date, user_id)
    elif report_type == 'custom':
        generator = CustomReportGenerator(report_type, start_date, end_date, user_id, custom_params)
    else:
        return {
            'status': 'error',
            'error': f'未知的报表类型: {report_type}'
        }
    
    # 生成报表
    return generator.generate()

# 快速测试
if __name__ == "__main__":
    print("测试生成统计报告...")
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    result = generate_report('statistics', start_date)
    print(f"报表生成结果: {result}") 
