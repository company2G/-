from app_simple import app, get_db
import re
from flask import request, render_template

def fix_statistics_final():
    """根据实际数据库结构修复统计报表功能"""
    
    print("开始修复统计报表功能...")
    
    # 读取app_simple.py文件
    with open('app_simple.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建备份
    with open('app_simple.py.stats_final_bak', 'w', encoding='utf-8') as f:
        f.write(content)
    print("创建了app_simple.py的备份")
    
    # 查找admin_statistics函数
    stats_pattern = r'(@app\.route\(\'/admin/statistics\'.*?def admin_statistics\(\):.*?)(?=\n@app\.route|\Z)'
    stats_match = re.search(stats_pattern, content, re.DOTALL)
    
    if stats_match:
        print("找到admin_statistics函数，准备修复...")
        old_stats = stats_match.group(1)
        
        # 创建修复后的函数，根据实际数据库结构
        new_stats = """@app.route('/admin/statistics')
@login_required
@admin_required
def admin_statistics():
    db = get_db()
    
    # 获取筛选参数
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # 新增产品统计 - 产品表没有创建者字段
    new_products = db.execute(
        'SELECT * FROM product ORDER BY id DESC'
    ).fetchall()
    
    # 产品使用统计
    usage_filter = ''
    usage_params = []
    
    if start_date:
        usage_filter += ' AND date(cpu.usage_date) >= ?'
        usage_params.append(start_date)
    
    if end_date:
        usage_filter += ' AND date(cpu.usage_date) <= ?'
        usage_params.append(end_date)
    
    product_usage = db.execute(
        'SELECT p.name, COUNT(cpu.id) as usage_count, SUM(cpu.amount_used) as total_used '
        'FROM client_product_usage cpu '
        'JOIN client_product cp ON cpu.client_product_id = cp.id '
        'JOIN product p ON cp.product_id = p.id '
        f'WHERE 1=1 {usage_filter} '
        'GROUP BY p.id '
        'ORDER BY total_used DESC',
        usage_params
    ).fetchall()
    
    # 操作人员使用统计
    try:
        operator_usage = db.execute(
            'SELECT o.id, o.name as operator_name, o.position, '
            'COUNT(cpu.id) as usage_count, SUM(cpu.amount_used) as total_used, '
            'COUNT(DISTINCT cp.client_id) as client_count, '
            'COUNT(DISTINCT cp.product_id) as product_type_count '
            'FROM client_product_usage cpu '
            'JOIN operators o ON cpu.operator_id = o.id '
            'JOIN client_product cp ON cpu.client_product_id = cp.id '
            f'WHERE 1=1 {usage_filter} '
            'GROUP BY o.id '
            'ORDER BY total_used DESC',
            usage_params
        ).fetchall()
    except Exception as e:
        # 如果查询出错，使用空列表
        operator_usage = []
        print(f"操作人员使用统计查询出错: {e}")
    
    # 无操作人员的使用记录统计（按记录人统计）
    try:
        no_operator_usage = db.execute(
            'SELECT u.id, u.username, u.role, '
            'COUNT(cpu.id) as usage_count, SUM(cpu.amount_used) as total_used, '
            'COUNT(DISTINCT cp.client_id) as client_count '
            'FROM client_product_usage cpu '
            'JOIN user u ON cpu.user_id = u.id '
            'JOIN client_product cp ON cpu.client_product_id = cp.id '
            f'WHERE cpu.operator_id IS NULL {usage_filter} '
            'GROUP BY u.id '
            'ORDER BY total_used DESC',
            usage_params
        ).fetchall()
    except Exception as e:
        # 如果查询出错，使用空列表
        no_operator_usage = []
        print(f"无操作人员使用记录统计查询出错: {e}")
    
    # 新增客户统计 - 包含创建者信息
    new_clients = db.execute(
        'SELECT c.*, u.username as creator_name '
        'FROM client c '
        'LEFT JOIN user u ON c.user_id = u.id '
        'ORDER BY c.id DESC'
    ).fetchall()
    
    # 归因统计 - 基于client表的user_id字段
    attribution_stats = db.execute(
        'SELECT u.username, COUNT(c.id) as client_count '
        'FROM client c '
        'JOIN user u ON c.user_id = u.id '
        'GROUP BY c.user_id '
        'ORDER BY client_count DESC'
    ).fetchall()
    
    return render_template(
        'admin/statistics.html',
        new_products=new_products,
        product_usage=product_usage,
        operator_usage=operator_usage,
        no_operator_usage=no_operator_usage,
        new_clients=new_clients,
        attribution_stats=attribution_stats,
        start_date=start_date,
        end_date=end_date
    )"""
        
        # 替换函数
        content = content.replace(old_stats, new_stats)
        print("已修复admin_statistics函数，适配实际数据库结构")
    else:
        print("未找到admin_statistics函数，请检查代码")
    
    # 确保导入request和render_template
    if 'from flask import ' in content and 'request' not in content:
        content = content.replace('from flask import ', 'from flask import request, ')
    
    # 写回文件
    with open('app_simple.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("已完成对统计功能的修复，请重启应用以应用更改")

if __name__ == "__main__":
    fix_statistics_final()