from app_simple import app, get_db
import re

def fix_statistics_with_creator():
    """修复统计报表并保留创建者信息"""
    
    # 首先检查数据库实际结构
    with app.app_context():
        db = get_db()
        
        # 检查product表结构
        product_columns = db.execute("PRAGMA table_info(product)").fetchall()
        product_column_names = [col[1] for col in product_columns]
        print("产品表列名:", product_column_names)
        
        # 检查是否有存储创建者的字段
        creator_field_product = None
        possible_creator_fields = ['created_by', 'creator', 'creator_id', 'user_id']
        for field in possible_creator_fields:
            if field in product_column_names:
                creator_field_product = field
                print(f"找到产品表创建者字段: {field}")
                break
        
        # 检查client表结构
        client_columns = db.execute("PRAGMA table_info(client)").fetchall()
        client_column_names = [col[1] for col in client_columns]
        print("客户表列名:", client_column_names)
        
        # 检查是否有存储创建者的字段
        creator_field_client = None
        for field in possible_creator_fields:
            if field in client_column_names:
                creator_field_client = field
                print(f"找到客户表创建者字段: {field}")
                break
        
        # 检查使用情况
        try:
            # 尝试获取一条产品记录来检查
            product = db.execute('SELECT * FROM product LIMIT 1').fetchone()
            if product:
                print("产品示例:", dict(product))
                
            # 尝试获取一条客户记录来检查
            client = db.execute('SELECT * FROM client LIMIT 1').fetchone()
            if client:
                print("客户示例:", dict(client))
        except Exception as e:
            print(f"检查表数据时出错: {e}")
    
    # 读取app_simple.py文件
    with open('app_simple.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建备份
    with open('app_simple.py.stats_creator_bak', 'w', encoding='utf-8') as f:
        f.write(content)
    print("创建了app_simple.py的备份")
    
    # 查找admin_statistics函数
    stats_pattern = r'(@app\.route\(\'/admin/statistics\'.*?def admin_statistics\(\):.*?)(?=\n@app\.route|\Z)'
    stats_match = re.search(stats_pattern, content, re.DOTALL)
    
    if stats_match:
        print("找到admin_statistics函数，准备修复...")
        old_stats = stats_match.group(1)
        
        # 构建产品查询
        product_query = 'SELECT p.*'
        product_join = ''
        
        if creator_field_product:
            product_query = f'SELECT p.*, u.username as creator_name'
            product_join = f'LEFT JOIN user u ON p.{creator_field_product} = u.id'
        
        # 构建客户查询
        client_query = 'SELECT c.*'
        client_join = ''
        
        if creator_field_client:
            client_query = f'SELECT c.*, u.username as creator_name'
            client_join = f'LEFT JOIN user u ON c.{creator_field_client} = u.id'
        
        # 创建修复后的函数，使用实际存在的列
        new_stats = f"""@app.route('/admin/statistics')
@login_required
@admin_required
def admin_statistics():
    db = get_db()
    
    # 获取筛选参数
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # 新增产品统计 - 尝试保留创建者信息
    new_products = db.execute(
        '{product_query} '
        'FROM product p '
        '{product_join} '
        'ORDER BY p.id DESC'
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
        f'WHERE 1=1 {{usage_filter}} '
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
            f'WHERE 1=1 {{usage_filter}} '
            'GROUP BY o.id '
            'ORDER BY total_used DESC',
            usage_params
        ).fetchall()
    except Exception as e:
        # 如果查询出错，使用空列表
        operator_usage = []
        print(f"操作人员使用统计查询出错: {{e}}")
    
    # 无操作人员的使用记录统计（按记录人统计）
    try:
        no_operator_usage = db.execute(
            'SELECT u.id, u.username, u.role, '
            'COUNT(cpu.id) as usage_count, SUM(cpu.amount_used) as total_used, '
            'COUNT(DISTINCT cp.client_id) as client_count '
            'FROM client_product_usage cpu '
            'JOIN user u ON cpu.user_id = u.id '
            'JOIN client_product cp ON cpu.client_product_id = cp.id '
            f'WHERE cpu.operator_id IS NULL {{usage_filter}} '
            'GROUP BY u.id '
            'ORDER BY total_used DESC',
            usage_params
        ).fetchall()
    except Exception as e:
        # 如果查询出错，使用空列表
        no_operator_usage = []
        print(f"无操作人员使用记录统计查询出错: {{e}}")
    
    # 新增客户统计 - 尝试保留创建者信息
    new_clients = db.execute(
        '{client_query} '
        'FROM client c '
        '{client_join} '
        'ORDER BY c.id DESC'
    ).fetchall()
    
    # 归因统计 - 如果能获取创建者信息
    attribution_stats = []
    if creator_field_client:
        try:
            attribution_stats = db.execute(
                'SELECT u.username, COUNT(c.id) as client_count '
                'FROM client c '
                'JOIN user u ON c.{creator_field_client} = u.id '
                'GROUP BY c.{creator_field_client} '
                'ORDER BY client_count DESC'
            ).fetchall()
        except Exception as e:
            print(f"归因统计查询出错: {{e}}")
    
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
        print("已修复admin_statistics函数，保留创建者信息")
    else:
        print("未找到admin_statistics函数，请检查代码")
    
    # 写回文件
    with open('app_simple.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("已完成对统计功能的修复，请重启应用以应用更改")

if __name__ == "__main__":
    fix_statistics_with_creator() 